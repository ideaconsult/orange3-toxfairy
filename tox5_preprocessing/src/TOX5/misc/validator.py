class Validator:
    ENDPOINTS = ['CTG', 'Casp', 'Dapi', 'H2AX', '8OHG']

    @staticmethod
    def raise_error_for_empty_str(string, message):
        if string.strip() == '':
            raise ValueError(message)

    @staticmethod
    def raise_error_for_uncorrect_endpoint(endpoint, message):
        if endpoint not in Validator.ENDPOINTS:
            raise ValueError(message)

