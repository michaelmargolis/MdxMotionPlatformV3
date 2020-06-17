"""
code_decode.py

Create and parse NL2 telemetry messages
see NL2 documentation for message format

"""

    
    def create_simple_message(self, msgId, requestId):  # message with no data
        result = pack('>cHIHc', 'N', msgId, requestId, 0, 'L')
        return result

    def create_NL2_message(self, msgId, requestId, msg):  # message is packed
        #  fields are: N Message Id, reqest Id, data size, L
        start = pack('>cHIH', 'N', msgId, requestId, len(msg))
        end = pack('>c', 'L')
        result = start + msg + end
        return result
