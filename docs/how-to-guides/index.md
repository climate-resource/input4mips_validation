# How-to guides

This part of the project documentation
focuses on a **problem-oriented** approach.
We'll go over how to solve common tasks.

## How can I prepare my input4MIPs files for publication on ESGF?

If you want to prepare your input4MIPs files so they can be published on ESGF,
you're in the right place.

[TODO: first step, demo how to write a file]

Once you have a file, or files, the next step is making sure that they pass validation.
The validation process is described in
["How to validate a single file"](how-to-validate-a-single-file).

After you have files which pass validation, you have two options:

1. Re-write your file according to the input4MIPs data reference syntax (DRS)
   (see
    ["How to write a file in the DRS"](how-to-write-a-single-file-in-the-drs)).
   Then, upload your file to LLNL's FTP server
   (see [TODO]).
   The benefit of this approach is that you will have a copy of the exact file
   that ends up on the ESGF.
   The downside is that you have to do an extra step.

1. Simply upload your file to LLNL's FTP server
   (see [TODO]).
   The benefit of this approach is that you have one less step to do.
   The downside is that your file will be re-written by the publication team,
   so you won't have a copy of the exact file that ends up on the ESGF
   (unless your file was absolutely perfect, in which case we simply
    put it in a different directory, we don't re-write it).

## How to work with a database of files?

[Relevant issue: #39](https://github.com/climate-resource/input4mips_validation/issues/39)

### Creating the database in the first place

Coming soon :)

- recommend using the validation flag, but don't have to
- rolls over the files, creates database entry for each
    - only works if the files follow the DRS
- writes out the database
  (currently as JSON, whether that's smart or not is a different question)

### Adding new entries to the database

Coming soon :)

- use the command

### Removing entries from the database

Coming soon :)

- not implemented because use case unclear

### Validating entries in the database

Coming soon :)

- use the command
- `--check-sha` flag to force checking of sha
  (slower, because you have to re-hash everything,
  but maybe worth doing sometimes)
- `--force` flag to force re-validation of everything
