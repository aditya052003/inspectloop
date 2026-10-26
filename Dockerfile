FROM public.ecr.aws/lambda/python:3.12
COPY requirements.txt ${LAMBDA_TASK_ROOT}/
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py vision.py demo.py storage.py lambda_handler.py ${LAMBDA_TASK_ROOT}/
COPY static ${LAMBDA_TASK_ROOT}/static
COPY templates ${LAMBDA_TASK_ROOT}/templates
CMD ["lambda_handler.handler"]
