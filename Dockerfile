FROM ghcr.io/towndex/towndex:latest

ADD action.py /action.py

ENTRYPOINT ["/action.py"]
