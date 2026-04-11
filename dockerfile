FROM python:3.12.3

WORKDIR /dir

COPY rec.txt .
RUN pip install --no-cache-dir -r rec.txt

COPY . .

ENV PORT=8070
EXPOSE 8070

CMD [ "uvicorn", "src.core.app:app", "--reload", "--host", "0.0.0.0", "--port", "8070" ]