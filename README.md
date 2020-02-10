# Pybart

## Pyacq

[Pyacq](https://github.com/pyacq/pyacq.git) is an open-source system for distributed data acquisition and stream processing.
This tutorial will help you to install pyacq and to be able to work on it.

## Pyacq installation


**Visual Studio 2017 must be installed.**


# Install dependencies packages

```bash
pip install pyzmq pytest numpy scipy pyqtgraph vispy colorama msgpack-python blosc pyqt5
```

Download Pyaudio File "PyAudio‑0.2.11‑cpXX‑cpXXm‑win_amd64.whl" based on your Python 3 version [here](https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio).

Use the package manager [pip](https://pip.pypa.io/en/stable/) to install Pyaudio.

```bash
pip install PyAudio‑0.2.11‑cpXX‑cpXXm‑win_amd64.whl
```

Use the [git](https://git-scm.com/downloads/) to clone Pyacq in your project folder and intall it.

```bash
# into your project folder
git clone https://github.com/pyacq/pyacq.git
pip install -e ./pyacq/
```
