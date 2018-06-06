"""JSON Encoding Rules (JER) codec.

"""

import json
import binascii
import math
import logging

from . import EncodeError
from . import DecodeError
from . import compiler
from .compiler import enum_values_as_dict


LOGGER = logging.getLogger(__name__)


class Type(object):

    def __init__(self, name, type_name):
        self.name = name
        self.type_name = type_name
        self.optional = False
        self.default = None

    def set_size_range(self, minimum, maximum, has_extension_marker):
        pass


class Integer(Type):

    def __init__(self, name):
        super(Integer, self).__init__(name, 'INTEGER')

    def encode(self, data):
        return data

    def decode(self, data):
        return data

    def __repr__(self):
        return 'Integer({})'.format(self.name)


class Real(Type):

    def __init__(self, name):
        super(Real, self).__init__(name, 'REAL')

    def encode(self, data):
        if data == float('inf'):
            return 'INF'
        elif data == float('-inf'):
            return '-INF'
        elif math.isnan(data):
            return 'NaN'
        else:
            return data

    def decode(self, data):
        if isinstance(data, float):
            return data
        else:
            return {
                'INF': float('inf'),
                '-INF': float('-inf'),
                'NaN': float('nan'),
                '0': 0.0,
                '-0': 0.0
            }[data]

    def __repr__(self):
        return 'Real({})'.format(self.name)


class Boolean(Type):

    def __init__(self, name):
        super(Boolean, self).__init__(name, 'BOOLEAN')

    def encode(self, data):
        return data

    def decode(self, data):
        return data

    def __repr__(self):
        return 'Boolean({})'.format(self.name)


class IA5String(Type):

    def __init__(self, name):
        super(IA5String, self).__init__(name, 'IA5String')

    def encode(self, data):
        return data

    def decode(self, data):
        return data

    def __repr__(self):
        return 'IA5String({})'.format(self.name)


class NumericString(Type):

    def __init__(self, name):
        super(NumericString, self).__init__(name, 'NumericString')

    def encode(self, data):
        return data

    def decode(self, data):
        return data

    def __repr__(self):
        return 'NumericString({})'.format(self.name)


class Sequence(Type):

    def __init__(self, name, members):
        super(Sequence, self).__init__(name, 'SEQUENCE')
        self.members = members

    def encode(self, data):
        values = {}

        for member in self.members:
            name = member.name

            if name in data:
                value = member.encode(data[name])
            elif member.optional or member.default is not None:
                continue
            else:
                raise EncodeError(
                    "Sequence member '{}' not found in {}.".format(
                        name,
                        data))

            values[name] = value

        return values

    def decode(self, data):
        values = {}

        for member in self.members:
            name = member.name

            if name in data:
                value = member.decode(data[name])
                values[name] = value
            elif member.optional:
                pass
            elif member.default is not None:
                values[name] = member.default

        return values

    def __repr__(self):
        return 'Sequence({}, [{}])'.format(
            self.name,
            ', '.join([repr(member) for member in self.members]))


class Set(Type):

    def __init__(self, name, members):
        super(Set, self).__init__(name, 'SET')
        self.members = members

    def encode(self, data):
        values = {}

        for member in self.members:
            name = member.name

            if name in data:
                if member.default is None:
                    value = member.encode(data[name])
                elif data[name] != member.default:
                    value = member.encode(data[name])
            elif member.optional or member.default is not None:
                continue
            else:
                raise EncodeError(
                    "Set member '{}' not found in {}.".format(
                        name,
                        data))

            values[name] = value

        return values

    def decode(self, data):
        values = {}

        for member in self.members:
            name = member.name

            if name in data:
                value = member.decode(data[name])
                values[name] = value
            elif member.optional:
                pass
            elif member.default is not None:
                values[name] = member.default

        return values

    def __repr__(self):
        return 'Set({}, [{}])'.format(
            self.name,
            ', '.join([repr(member) for member in self.members]))


class SequenceOf(Type):

    def __init__(self, name, element_type):
        super(SequenceOf, self).__init__(name, 'SEQUENCE OF')
        self.element_type = element_type

    def encode(self, data):
        values = []

        for entry in data:
            value = self.element_type.encode(entry)
            values.append(value)

        return values

    def decode(self, data):
        values = []

        for element_data in data:
            value = self.element_type.decode(element_data)
            values.append(value)

        return values

    def __repr__(self):
        return 'SequenceOf({}, {})'.format(self.name,
                                           self.element_type)


class SetOf(Type):

    def __init__(self, name, element_type):
        super(SetOf, self).__init__(name, 'SET OF')
        self.element_type = element_type

    def encode(self, data):
        values = []

        for entry in data:
            value = self.element_type.encode(entry)
            values.append(value)

        return values

    def decode(self, data):
        values = []

        for element_data in data:
            value = self.element_type.decode(element_data)
            values.append(value)

        return values

    def __repr__(self):
        return 'SetOf({}, {})'.format(self.name,
                                      self.element_type)


class BitString(Type):

    def __init__(self, name, minimum, maximum):
        super(BitString, self).__init__(name, 'BIT STRING')

        if minimum is None and maximum is None:
            self.size = None
        elif minimum == maximum:
            self.size = minimum
        else:
            self.size = None

    def encode(self, data):
        value = binascii.hexlify(data[0]).decode('ascii')

        if self.size is None:
            value = {
                "value": value,
                "length": data[1]
            }

        return value

    def decode(self, data):
        if self.size is None:
            return (binascii.unhexlify(data['value']), data['length'])
        else:
            return (binascii.unhexlify(data), self.size)

    def __repr__(self):
        return 'BitString({})'.format(self.name)


class OctetString(Type):

    def __init__(self, name):
        super(OctetString, self).__init__(name, 'OCTET STRING')

    def encode(self, data):
        return binascii.hexlify(data).decode('ascii')

    def decode(self, data):
        return binascii.unhexlify(data)

    def __repr__(self):
        return 'OctetString({})'.format(self.name)


class PrintableString(Type):

    def __init__(self, name):
        super(PrintableString, self).__init__(name, 'PrintableString')

    def encode(self, data):
        return data

    def decode(self, data):
        return data

    def __repr__(self):
        return 'PrintableString({})'.format(self.name)


class UniversalString(Type):

    def __init__(self, name):
        super(UniversalString, self).__init__(name, 'UniversalString')

    def encode(self, data):
        return data

    def decode(self, data):
        return data

    def __repr__(self):
        return 'UniversalString({})'.format(self.name)


class VisibleString(Type):

    def __init__(self, name):
        super(VisibleString, self).__init__(name, 'VisibleString')

    def encode(self, data):
        return data

    def decode(self, data):
        return data

    def __repr__(self):
        return 'VisibleString({})'.format(self.name)


class GeneralString(Type):

    def __init__(self, name):
        super(GeneralString, self).__init__(name, 'GeneralString')

    def encode(self, data):
        return data

    def decode(self, data):
        return data

    def __repr__(self):
        return 'GeneralString({})'.format(self.name)


class UTF8String(Type):

    def __init__(self, name):
        super(UTF8String, self).__init__(name, 'UTF8String')

    def encode(self, data):
        return data

    def decode(self, data):
        return data

    def __repr__(self):
        return 'UTF8String({})'.format(self.name)


class BMPString(Type):

    def __init__(self, name):
        super(BMPString, self).__init__(name, 'BMPString')

    def encode(self, data):
        return data.decode('ascii')

    def decode(self, data):
        return data.encode('ascii')

    def __repr__(self):
        return 'BMPString({})'.format(self.name)


class GraphicString(Type):

    def __init__(self, name):
        super(GraphicString, self).__init__(name, 'GraphicString')

    def encode(self, data):
        return data

    def decode(self, data):
        return data

    def __repr__(self):
        return 'GraphicString({})'.format(self.name)


class UTCTime(Type):

    def __init__(self, name):
        super(UTCTime, self).__init__(name, 'UTCTime')

    def encode(self, data):
        return data

    def decode(self, data):
        return data

    def __repr__(self):
        return 'UTCTime({})'.format(self.name)


class GeneralizedTime(Type):

    def __init__(self, name):
        super(GeneralizedTime, self).__init__(name, 'GeneralizedTime')

    def encode(self, data):
        return data

    def decode(self, data):
        return data

    def __repr__(self):
        return 'GeneralizedTime({})'.format(self.name)


class TeletexString(Type):

    def __init__(self, name):
        super(TeletexString, self).__init__(name, 'TeletexString')

    def encode(self, data):
        return data.decode('ascii')

    def decode(self, data):
        return data.encode('ascii')

    def __repr__(self):
        return 'TeletexString({})'.format(self.name)


class ObjectIdentifier(Type):

    def __init__(self, name):
        super(ObjectIdentifier, self).__init__(name, 'OBJECT IDENTIFIER')

    def encode(self, data):
        return data

    def decode(self, data):
        return data

    def __repr__(self):
        return 'ObjectIdentifier({})'.format(self.name)


class Choice(Type):

    def __init__(self, name, members):
        super(Choice, self).__init__(name, 'CHOICE')
        self.members = members
        self.name_to_member = {member.name: member for member in self.members}

    def encode(self, data):
        try:
            member = self.name_to_member[data[0]]
        except KeyError:
            raise EncodeError(
                "Expected choices are {}, but got '{}'.".format(
                    sorted([member.name for member in self.members]),
                    data[0]))

        return {member.name: member.encode(data[1])}

    def decode(self, data):
        name, value = list(data.items())[0]

        try:
            member = self.name_to_member[name]
        except KeyError:
            raise DecodeError(
                "Expected choices are {}, but got '{}'.".format(
                    sorted([member.name for member in self.members]),
                    name))

        return (name, member.decode(value))

    def __repr__(self):
        return 'Choice({}, [{}])'.format(
            self.name,
            ', '.join([repr(member) for member in self.members]))


class Null(Type):

    def __init__(self, name):
        super(Null, self).__init__(name, 'NULL')

    def encode(self, data):
        return data

    def decode(self, data):
        return data

    def __repr__(self):
        return 'Null({})'.format(self.name)


class Any(Type):

    def __init__(self, name):
        super(Any, self).__init__(name, 'ANY')

    def encode(self, _, encoder):
        raise NotImplementedError('ANY is not yet implemented.')

    def decode(self, data):
        raise NotImplementedError('ANY is not yet implemented.')

    def __repr__(self):
        return 'Any({})'.format(self.name)


class Enumerated(Type):

    def __init__(self, name, values):
        super(Enumerated, self).__init__(name, 'ENUMERATED')
        self.values = set(enum_values_as_dict(values).values())

    def encode(self, data):
        if data not in self.values:
            raise EncodeError(
                "Enumeration value '{}' not found in {}.".format(
                    data[0],
                    sorted(list(self.values))))

        return data

    def decode(self, data):
        if data not in self.values:
            raise DecodeError(
                "Enumeration value '{}' not found in {}.".format(
                    data,
                    sorted(list(self.values))))

        return data

    def __repr__(self):
        return 'Enumerated({})'.format(self.name)


class Recursive(Type, compiler.Recursive):

    def __init__(self, name, type_name, module_name):
        super(Recursive, self).__init__(name, 'RECURSIVE')
        self.type_name = type_name
        self.module_name = module_name
        self._inner = None

    def set_inner_type(self, inner):
        self._inner = inner

    def encode(self, data):
        return self._inner.encode(data)

    def decode(self, data):
        return self._inner.decode(data)

    def __repr__(self):
        return 'Recursive({})'.format(self.name)


class CompiledType(compiler.CompiledType):

    def __init__(self, type_, constraints):
        super(CompiledType, self).__init__(constraints)
        self._type = type_

    @property
    def type(self):
        return self._type

    def encode(self, data, indent=None):
        dictionary = self._type.encode(data)

        if indent is None:
            string = json.dumps(dictionary, separators=(',', ':'))
        else:
            string = json.dumps(dictionary, indent=indent)

        return string.encode('utf-8')

    def decode(self, data):
        return self._type.decode(json.loads(data.decode('utf-8')))

    def __repr__(self):
        return repr(self._type)


class Compiler(compiler.Compiler):

    def process_type(self, type_name, type_descriptor, module_name):
        compiled_type = self.compile_type(type_name,
                                          type_descriptor,
                                          module_name)
        constraints = self.compile_constraints(type_name,
                                               type_descriptor,
                                               module_name)

        return CompiledType(compiled_type, constraints)

    def compile_type(self, name, type_descriptor, module_name):
        type_name = type_descriptor['type']

        if type_name == 'SEQUENCE':
            members = self.compile_members(
                type_descriptor['members'],
                module_name)
            compiled = Sequence(name, members)
        elif type_name == 'SEQUENCE OF':
            compiled = SequenceOf(name,
                                  self.compile_type('',
                                                    type_descriptor['element'],
                                                    module_name))
        elif type_name == 'SET':
            members = self.compile_members(
                type_descriptor['members'],
                module_name)
            compiled = Set(name, members)
        elif type_name == 'SET OF':
            compiled = SetOf(name,
                             self.compile_type('',
                                               type_descriptor['element'],
                                               module_name))
        elif type_name == 'CHOICE':
            members = self.compile_members(
                type_descriptor['members'],
                module_name)
            compiled = Choice(name, members)
        elif type_name == 'INTEGER':
            compiled = Integer(name)
        elif type_name == 'REAL':
            compiled = Real(name)
        elif type_name == 'ENUMERATED':
            compiled = Enumerated(name, type_descriptor['values'])
        elif type_name == 'BOOLEAN':
            compiled = Boolean(name)
        elif type_name == 'OBJECT IDENTIFIER':
            compiled = ObjectIdentifier(name)
        elif type_name == 'OCTET STRING':
            compiled = OctetString(name)
        elif type_name == 'TeletexString':
            compiled = TeletexString(name)
        elif type_name == 'NumericString':
            compiled = NumericString(name)
        elif type_name == 'PrintableString':
            compiled = PrintableString(name)
        elif type_name == 'IA5String':
            compiled = IA5String(name)
        elif type_name == 'VisibleString':
            compiled = VisibleString(name)
        elif type_name == 'GeneralString':
            compiled = GeneralString(name)
        elif type_name == 'UTF8String':
            compiled = UTF8String(name)
        elif type_name == 'BMPString':
            compiled = BMPString(name)
        elif type_name == 'GraphicString':
            compiled = GraphicString(name)
        elif type_name == 'UTCTime':
            compiled = UTCTime(name)
        elif type_name == 'UniversalString':
            compiled = UniversalString(name)
        elif type_name == 'GeneralizedTime':
            compiled = GeneralizedTime(name)
        elif type_name == 'BIT STRING':
            minimum, maximum, _ = self.get_size_range(type_descriptor,
                                                      module_name)
            compiled = BitString(name, minimum, maximum)
        elif type_name == 'ANY':
            compiled = Any(name)
        elif type_name == 'ANY DEFINED BY':
            compiled = Any(name)
        elif type_name == 'NULL':
            compiled = Null(name)
        else:
            if type_name in self.types_backtrace:
                compiled = Recursive(name,
                                     type_name,
                                     module_name)
                self.recursive_types.append(compiled)
            else:
                compiled = self.compile_user_type(name,
                                                  type_name,
                                                  module_name)

        return compiled


def compile_dict(specification):
    return Compiler(specification).process()


def decode_length(_data):
    raise DecodeError('Decode length is not supported for this codec.')
