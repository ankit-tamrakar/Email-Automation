# Email Automation

## How to run
Navigate to the root directory using the ```cd``` command. 
Run the program by running the following command:
```python src/main.py```

## Understand the application logs

The application logs can be found under ```logs``` directory. Each log file is a day specific file named email_automation_<current_date>.log format.

The log messages are in the following format:
```timestamp``` ```file_name```:```line_number``` ```LEVEL```

The logs have 3 different levels:
1. ```INFO``` - basic success messages.
2. ```ERROR``` - error messages from the API Response like 401 Unauthorized error.
3. ```CRITICAL``` - coding errors or file not found errors. Example - reading a file which does not exists.

Debug/troubleshoot the error by reading the error message carefully.
For example: 
```2025-03-15 11:18:02,964 main.py:14 CRITICAL: File not found at src/config/introduction_email.txt. Exception caught - [Errno 2] No such file or directory: 'src/config/introduction_email.txt'```

The above error message indicates that the code was executed at ```2025-03-15 11:18:02,964 ``` and the execption/error message was written to the log file by the ```main``` file's ```line number 14```. The message states that the file ```introduction_email.txt``` was not found at the mentioned location.

