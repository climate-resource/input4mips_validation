- test of metadata class
    - test that the metadata is validated on initialisation, e.g. `assert_input4mips_ds_metadata_is_valid`
        - test fail in source ID and activity ID consistency
        - test activity ID inference

- then the validator of the data set class can just focus on data <-> metadata consistency
    - test that variable name matches the metadata
    - etc. ...

- switch to getting directory and filename from the CVs
    - update the DRS so that version comes from the metadata, rather than being a date string
    - add a check that the path only contains [a-zA-Z0-9-] before writing

- inference
    - create an `Input4MIPsMetadataDataProducerMinimum` class
    - add a `from_input4mips_data_producer_minimum` method to `Input4MIPsMetadata`
        - can use e.g. inference of fields from the source ID

    - test activity ID inference

- to explain this
    - you're basically splitting the full data model from the bits that data producers need to understand
    - PD and I will have to understand full data model
    - everyone else just needs to worry about the minimum stuff, but are welcome to read full thing if they want
