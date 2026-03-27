FROM alpine:edge

RUN apk --update add --no-cache python3 py3-pip openssl ca-certificates build-base python3-dev
WORKDIR /EmailHarvester

COPY . /EmailHarvester

RUN python3 -m venv /venv
ENV PATH="/venv/bin:$PATH"
RUN pip install --no-cache-dir -r requirements.txt

ENTRYPOINT ["python3", "EmailHarvester.py"]
CMD ["-h"]
