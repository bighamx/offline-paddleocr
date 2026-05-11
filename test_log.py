import os
import logging
os.environ['GLOG_minloglevel']='2'
import warnings
warnings.filterwarnings('ignore')
import paddlex
paddlex.utils.logging.setup_logging('ERROR')
from common import run_ocr
run_ocr('sample.png')
