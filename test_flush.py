import sys, os, contextlib

@contextlib.contextmanager
def suppress_stdout_stderr_fd():
    null_fd = os.open(os.devnull, os.O_RDWR)
    old_stdout, old_stderr = sys.stdout, sys.stderr
    sys.stdout = open(os.devnull, 'w')
    sys.stderr = open(os.devnull, 'w')
    
    try:
        save_fd_out = os.dup(1)
        save_fd_err = os.dup(2)
        os.dup2(null_fd, 1)
        os.dup2(null_fd, 2)
    except OSError:
        save_fd_out = save_fd_err = None

    try:
        yield
    finally:
        sys.stdout.flush()
        sys.stderr.flush()
        old_stdout.flush()
        old_stderr.flush()
        if save_fd_out is not None:
            os.dup2(save_fd_out, 1)
            os.close(save_fd_out)
        if save_fd_err is not None:
            os.dup2(save_fd_err, 2)
            os.close(save_fd_err)
        os.close(null_fd)
        sys.stdout.close()
        sys.stderr.close()
        sys.stdout, sys.stderr = old_stdout, old_stderr

with suppress_stdout_stderr_fd():
    from common import run_ocr
    payload = run_ocr('sample.png')
    
print(payload['text'][:20])
