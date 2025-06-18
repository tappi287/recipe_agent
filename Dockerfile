FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

ADD . /src

RUN uv sync --frozen

CMD ["uv", "run", "hello"]