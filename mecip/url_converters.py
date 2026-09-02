import base64
import uuid


def encode_public_id(public_id):
    public_uuid = (
        public_id
        if isinstance(public_id, uuid.UUID)
        else uuid.UUID(str(public_id))
    )
    return (
        base64.urlsafe_b64encode(public_uuid.bytes)
        .rstrip(b'=')
        .decode('ascii')
    )


def decode_public_id(token):
    decoded = base64.b64decode(
        token.encode('ascii') + b'==',
        altchars=b'-_',
        validate=True,
    )
    public_id = uuid.UUID(bytes=decoded)

    if encode_public_id(public_id) != token:
        raise ValueError('Token público inválido.')

    return public_id


class PublicIdConverter:
    regex = r'[A-Za-z0-9_-]{22}'

    def to_python(self, value):
        return decode_public_id(value)

    def to_url(self, value):
        return encode_public_id(value)
