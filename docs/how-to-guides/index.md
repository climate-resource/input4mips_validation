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

When using our [command-line interface][input4mips-validation].

We use [loguru](https://loguru.readthedocs.io/en/stable/)
to control our logging.



From the Python API, this makes activating the logging very easy.
All you need is code like the following

```python
from loguru import logger

logger.activate("input4MIPs_validation")
```
