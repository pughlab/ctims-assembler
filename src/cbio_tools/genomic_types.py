class CnvEventTypeEnum():
    """Used to filter CNV events by type in the following endpoint
    https://cbioportal.ca/cbioportal/api/swagger-ui/index.html?urls.primaryName=default#/Discrete%20Copy%20Number%20Alterations/fetchDiscreteCopyNumbersInMolecularProfileUsingPOST

    """
    ALL = 'ALL'
    AMP = 'AMP'
    DIPLOID = 'DIPLOID'
    GAIN = 'GAIN'
    HETLOSS = 'HETLOSS'
    HOMDEL = 'HOMDEL'
    HOMDEL_AND_AMP = 'HOMDEL_AND_AMP'
