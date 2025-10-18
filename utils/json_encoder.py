"""
Custom JSON Encoder and Renderer to handle infinity and NaN values
"""
import json
import math
from decimal import Decimal
from rest_framework.renderers import JSONRenderer
from rest_framework.utils.encoders import JSONEncoder as DRFJSONEncoder


class SafeJSONEncoder(DRFJSONEncoder):
    """
    Custom JSON encoder that safely handles infinity and NaN values
    by converting them to None or 0
    """
    
    def encode(self, o):
        """Override encode to sanitize data before encoding"""
        sanitized = self._sanitize(o)
        return super().encode(sanitized)
    
    def _sanitize(self, obj):
        """Recursively sanitize data to remove infinity and NaN values"""
        if isinstance(obj, dict):
            return {key: self._sanitize(value) for key, value in obj.items()}
        elif isinstance(obj, (list, tuple)):
            return [self._sanitize(item) for item in obj]
        elif isinstance(obj, float):
            # Check for infinity or NaN
            if math.isinf(obj) or math.isnan(obj):
                return 0.0
            return obj
        elif isinstance(obj, Decimal):
            # Convert Decimal to float and check for infinity
            try:
                float_val = float(obj)
                if math.isinf(float_val) or math.isnan(float_val):
                    return 0.0
                return obj
            except (ValueError, OverflowError):
                return 0.0
        else:
            return obj
    
    def iterencode(self, o, _one_shot=False):
        """Override iterencode to sanitize data before encoding"""
        sanitized = self._sanitize(o)
        return super().iterencode(sanitized, _one_shot=_one_shot)


class SafeJSONRenderer(JSONRenderer):
    """
    Custom JSON renderer that uses SafeJSONEncoder
    to handle infinity and NaN values
    """
    encoder_class = SafeJSONEncoder

