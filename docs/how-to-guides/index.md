# How-to guides

This part of the project documentation
focuses on a **problem-oriented** approach.
We'll go over how to solve common tasks.

## How can I prepare my input4MIPs files for publication on ESGF?

If you want to prepare your input4MIPs files so they can be published on ESGF,
you're in the right place.

### I am writing my file(s) from scratch

If you are writing your file(s) from scratch,
the first step is to write your file(s).
The file writing process using input4MIPs validation is described in
["How to write a single valid file"](how-to-write-a-single-valid-file).

The next step is to double check that your file(s) passes validation.
The validation process is described in
["How to validate a single file"](how-to-validate-a-single-file).

The last step is to upload your file(s) to LLNL's FTP server.
The upload process is described in
["How to upload to an FTP server"](how-to-upload-to-ftp).

### I already have a file(s) that I have written

If you have already written a file(s)
using a tool other than input4MIPs validation,
the next step is making sure that the file(s) passes validation.
The validation process is described in
["How to validate a single file"](how-to-validate-a-single-file).

After you have a file(s) which passes validation, you have two options:

1. Re-write your file(s) according to the input4MIPs data reference syntax (DRS)
   (see
    ["How to write a file in the DRS"](how-to-write-a-single-file-in-the-drs)).
   Then, upload your file(s) to LLNL's FTP server
   (see ["How to upload to an FTP server"](how-to-upload-to-ftp)).
   The benefit of this approach is that you will have a copy of the exact file(s)
   that ends up on the ESGF.
   The downside is that you have to do an extra step.

1. Simply upload your file(s) to LLNL's FTP server
   (see ["How to upload to an FTP server"](how-to-upload-to-ftp)).
   The benefit of this approach is that you have one less step to do.
   The downside is that your file(s) will be re-written by the publication team,
   so you won't have a copy of the exact file(s) that ends up on the ESGF
   (unless your file(s) was absolutely perfect, in which case we simply
    put it in a different directory, we don't re-write it).

## How to work with a database of files?

If you are planning on managing a database of files,
please take a look at ["How to manage a database"](how-to-manage-a-database).

## How to configure logging with input4MIPs-validation?

Logging in Python isn't as straightforward as it could be.
As a result, here we provide a guide to configuring logging with input4MIPs-validation.
We hope that, one day in the future, such a guide won't be needed
because logging will be done in a consistent way across the Python ecosystem.

If you are using our [command-line interface][input4mips-validation],
then please checkout the [command-line interface's docs][input4mips-validation]
for full details of the available logging configuration options.
In addition to those docs, below we also provide a sample of the configuration
which can be used with [loguru-config](https://github.com/erezinman/loguru-config).
For full details, see [loguru](https://loguru.readthedocs.io/)
and [loguru-config](https://github.com/erezinman/loguru-config).


```yaml
# A sample file, which illustrates how the logging can be configured
handlers:
  # Send messages to stderr
  - sink: ext://sys.stderr
    # Some other levels that might be useful
    # level: DEBUG
    # level: INFO_INDIVIDUAL_CHECK
    # level: INFO_INDIVIDUAL_CHECK_ERROR
    # level: INFO_FILE
    # level: INFO_FILE_ERROR
    level: INFO
    colorize: true
    format: "{process} - {thread} - <green>{time:!UTC}</> - <lvl>{level}</> - <cyan>{name}:{file}:{line}</> - <lvl>{message}</>"
  # Log to a file too
  - sink: file_{time}.log
    level: DEBUG
    enqueue: true
    format: "{process} - {thread} - {time:!UTC} - {level} - {name}:{file}:{line} - {message}"
activation:
  - [ "input4mips_validation", true ]
```

If you are using the Python API, by default, the logging is disabled
(in line with [best practice](https://loguru.readthedocs.io/en/stable/overview.html#suitable-for-scripts-and-libraries)).
This gives you, as the user, full control of the logging.
Activating the logging is very easy.
All you need is code like the following

```python
from loguru import logger

logger.activate("input4MIPs_validation")

# Apply any other configuration options you want too.
# See links to loguru's docs below for further details and examples.
```

All the usual loguru configuration can also be applied.
For full configuration options, see
[loguru's docs](https://loguru.readthedocs.io/en/stable/api/logger.html#loguru._logger.Logger.configure).
