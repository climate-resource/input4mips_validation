- switch to getting directory and filename from the CVs
    - update the DRS so that version comes from the metadata, rather than being a date string
    - add a check that the path only contains [a-zA-Z0-9-] before writing

- to explain this
    - you're basically splitting the full data model from the bits that data producers need to understand
    - PD and I will have to understand full data model
    - everyone else just needs to worry about the minimum stuff, but are welcome to read full thing if they want

- rest of tests for various keys etc.
