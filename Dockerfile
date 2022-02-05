FROM ghcr.io/towndex/gui:latest

ADD action.py /action.py

ENTRYPOINT ["/action.py"]
