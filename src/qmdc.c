
#include <Python.h>

#include <stdio.h>
#include <libgen.h>
#include <pthread.h>

#include <ao/ao.h>
#include <libavcodec/avcodec.h>


static AVCodecContext *avctx;
static ao_device *device;

static double play_gain = 0.0;


typedef struct packet {
  uint8_t *data;
  int size;
  
  struct packet *next;
} packet_t;

static packet_t *queue_head = NULL;
static packet_t *queue_tail = NULL;
static pthread_mutex_t queue_mutex = PTHREAD_MUTEX_INITIALIZER;
static pthread_t audio_thread;

static int queue_size = 0;
static int queue_cleared = 0;

static int thread_run = 0;


void clear_queue()
{
  packet_t *packet = NULL, *next_packet = NULL;
  
  packet = queue_head;
  if (queue_head) {
    next_packet = queue_head->next;
  }
  while (packet) {
    av_free(packet->data);
    free(packet);
    packet = next_packet;
    if (next_packet) {
      next_packet = next_packet->next;
    }
  }
  
  queue_head = NULL;
  queue_tail = NULL;
  
  queue_size = 0;
  
  queue_cleared = 1;
}

static void apply_gain(int16_t *buffer, int frames, double gain)
{
  for (; frames > 0; ++buffer, --frames) {
    *buffer *= gain;
  }
}

void *thread_func(void *data)
{
  (void)data;
  packet_t *packet;
  AVPacket pkt;
  int16_t buffer[AVCODEC_MAX_AUDIO_FRAME_SIZE];
  int frame_size;
  int result;
  int error_counter = 0;

  while (thread_run) {
    pthread_mutex_lock(&queue_mutex);
    if (!queue_head) {
      pthread_mutex_unlock(&queue_mutex);
      usleep(10 * 1000);
      continue;
    }
    packet = queue_head;
    queue_head = packet->next;
    queue_size -= packet->size;
    pthread_mutex_unlock(&queue_mutex);
    
    pkt.data = packet->data;
    pkt.size = packet->size;
    
    frame_size = AVCODEC_MAX_AUDIO_FRAME_SIZE;

    result = avcodec_decode_audio3(avctx, buffer, &frame_size, &pkt);
    if (result < 0) {
      printf("avcodec_decode_audio3: %s\n", strerror(AVUNERROR(result)));
      ++error_counter;
    } else {
      error_counter = 0;
    }
    
    /**
     * @todo FIXME At least some mp3 streams with missing header can't decode
     * first one or two packets, any better way to handle errors than this? */
    if (error_counter >= 10) {
      printf("Unable to decode, audio thread quitting.\n");
      return NULL;
    }

    free(packet->data);
    free(packet);
    
    if (play_gain > 0.0) {
      apply_gain(buffer, frame_size, play_gain);
    }
    
    ao_play(device, (char*)buffer, frame_size);
    /*usleep(frame_size / 2.0 / 44100.0 * 1000000 - 20 * 1000);*/
  }
  return NULL;
}


static PyObject *
mdc_open_sink(PyObject *self, PyObject *args, PyObject *keywds)
{
  (void)self;
  
  /* Required */
  char *codec;
  int samplerate;
  int channels;
  int bitspersample;
  
  /* Optional */
  double gain = 0.0;
  PyBytesObject *extradata = NULL;

  static char *kwlist[] = {"codec", "samplerate", "channels", "bitspersample", "gain",
                           "extradata", NULL};

  if (!PyArg_ParseTupleAndKeywords(args, keywds, "siii|dS", kwlist,
    &codec, &samplerate, &channels, &bitspersample, &gain, &extradata)) {
    return NULL;
  }

  if (thread_run) {
    thread_run = 0;
    pthread_join(audio_thread, NULL);
  }
  
  if (avctx) {
    clear_queue();
    avcodec_close(avctx);
  }
  
  printf("mdc_open_sink: codec: %s, samplerate: %i, channels: %i, bitspersample: %i\n",
    codec, samplerate, channels, bitspersample);
  
  avctx = avcodec_alloc_context();
  avctx->sample_rate = samplerate;
  avctx->channels = channels;

  if (extradata && PyBytes_Size((PyObject*)extradata) > 0) {
    avctx->extradata = (uint8_t*)PyBytes_AsString((PyObject*)extradata);
    avctx->extradata_size = PyBytes_Size((PyObject*)extradata);
  } else {
    avctx->extradata = NULL;
  }

  AVCodec *avcodec = avcodec_find_decoder_by_name(codec);
  if (!avcodec) {
    printf("ERROR: No such codec: '%s'.\n", codec);
    return NULL;
  }
  
  if (avcodec_open(avctx, avcodec) < 0) {
    printf("ERROR: Could not open decoder.\n");
    return NULL;
  }

  play_gain = gain;
  
  ao_sample_format format;
  int default_driver;

  default_driver = ao_default_driver_id();

  memset(&format, 0, sizeof(format));
  format.channels = avctx->channels;
  format.bits = bitspersample;
  format.rate = avctx->sample_rate;
  format.byte_format = AO_FMT_LITTLE;

  device = ao_open_live(default_driver, &format, NULL);

  thread_run = 1;
  pthread_create(&audio_thread, NULL, thread_func, NULL);
  
  
  Py_IncRef(Py_None);
  return Py_None;
}


static PyObject *
mdc_packet(PyObject *self, PyObject *args)
{
  (void)self;
  PyBytesObject *data;
  packet_t *packet;
  const char *pkt_data;
  int pkt_size;
  
  if (!PyArg_ParseTuple(args, "S", &data)) {
    return NULL;
  }
  
  pkt_data = PyBytes_AsString((PyObject*)data);
  pkt_size = PyBytes_Size((PyObject*)data);
  
  pthread_mutex_lock(&queue_mutex);
  
  /**
   * @todo FIXME Synch threads correctly for limiting buffer size.
   */
  /*queue_cleared = 0;
  
  Py_BEGIN_ALLOW_THREADS

  while (queue_size > 1024 * 1024) {
    pthread_mutex_unlock(&queue_mutex);
    sleep(1);
    pthread_mutex_lock(&queue_mutex);
  }
  
  Py_END_ALLOW_THREADS
  
  if (queue_cleared) {
    queue_cleared = 0;
  
    Py_IncRef(Py_None);
    pthread_mutex_unlock(&queue_mutex);
    return Py_None;
  }*/
  
  packet = malloc(sizeof(packet_t));
  packet->data = av_mallocz(pkt_size + FF_INPUT_BUFFER_PADDING_SIZE);
  memcpy(packet->data, pkt_data, pkt_size);
  packet->size = pkt_size;
  packet->next = NULL;
  
  if (!queue_head) {
    queue_head = packet;
    queue_tail = packet;
  } else {
    queue_tail->next = packet;
    queue_tail = packet;
  }
  
  queue_size += packet->size;
  
  pthread_mutex_unlock(&queue_mutex); 
  
  Py_IncRef(Py_None);
  return Py_None;
  
}

static PyObject *
mdc_flush(PyObject *self)
{ 
  (void)self;
  
  Py_BEGIN_ALLOW_THREADS
  pthread_mutex_lock(&queue_mutex); 

  clear_queue();
  
  avcodec_flush_buffers(avctx);
  
  pthread_mutex_unlock(&queue_mutex); 
  
  Py_END_ALLOW_THREADS
  
  Py_IncRef(Py_None);
  return Py_None;
}


static PyObject *
mdc_toggle_pause(PyObject *self)
{
  (void)self;
  
  Py_BEGIN_ALLOW_THREADS
  if (thread_run) {
    thread_run = 0;
    pthread_join(audio_thread, NULL);
  } else {
    thread_run = 1;
    pthread_create(&audio_thread, NULL, thread_func, NULL);
  }
  Py_END_ALLOW_THREADS
  
  Py_IncRef(Py_None);
  return Py_None;
}


static PyMethodDef mdc_methods[] = {
  {"open_sink", (PyCFunction)mdc_open_sink, METH_VARARGS | METH_KEYWORDS,
    "Open a sink for a stream."},
  {"packet", (PyCFunction)mdc_packet, METH_VARARGS,
    "Open a sink for a stream."},
  {"flush", (PyCFunction)mdc_flush, METH_NOARGS,
    "Flush buffers."},
  {"toggle_pause", (PyCFunction)mdc_toggle_pause, METH_NOARGS,
    "Toggle pause."},
  {NULL, NULL, 0, NULL}
};


PyMODINIT_FUNC init_mdc(void)
{
  Py_InitModule("mdc", mdc_methods);
}

int main(int argc, char *argv[])
{
  (void)argc;
  
  FILE* pyfile;
  
#ifndef RUN_IN_PLACE
  char buffer[BUFSIZ], *self, *base, *pypath;
  int len;
#endif
  
  Py_SetProgramName(argv[0]);
  PyImport_AppendInittab("mdc", init_mdc);
  Py_Initialize();

  ao_initialize();
  avcodec_register_all();

#ifdef RUN_IN_PLACE
  pyfile = fopen("qmdc.py", "r");
#else
  len = readlink("/proc/self/exe", buffer, BUFSIZ);
  buffer[len] = '\0';
  self = strdup(buffer);
  base = dirname(self);
  pypath = calloc(strlen(base) + 9, sizeof(char));
  
  sprintf(pypath, "%s/qmdc.py", base);
  
  pyfile = fopen(pypath, "r");
  free(self);
  free(pypath);
#endif
  
  PyRun_SimpleFile(pyfile, "qmdc.py");
  
  Py_Finalize();
  
  return 0;
}

