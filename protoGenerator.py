import argparse
import random
import inflect

# Taking command line arguments
parser = argparse.ArgumentParser(description="A simple script to generate large protofiles")
parser.add_argument("message_count", type=int, help="Number of messages")
parser.add_argument("field_count", type=int, help="Number of fields in each message")
parser.add_argument('-s', "--service", nargs=2, type=int, help="No of services + rpc per service you want")
parser.add_argument('-o', "--oneof", nargs=2, type=int, help="No of oneof's per message + fields per oneof that you want")
parser.add_argument('-e', "--enum", nargs=3, type=int, help="No of enums per messages + No of enums defined + fields per enum that you want")
parser.add_argument("--nested_message", action='store_true', help="Enables random nested messages")
parser.add_argument("--streaming", action='store_true', help="Enables random streaming rpc's")
parser.add_argument("--repeated", action='store_true', help="Enables random repeated messages")
parser.add_argument('-f', "--output", type=str, help="Name of the output txt file")

args = parser.parse_args()

# Convert a number to its string name
def number_to_words(number):
    p = inflect.engine()
    return p.number_to_words(number)

def generate_random_message(fields, index, message_count):

    # Start and end format of the protofile
    start = f"\nmessage Message{index} {{"
    end = f"\n}}\n"

    # Function to get random message fields with provided indentation
    def get_random_field(field_postfix, field_value, message_count, spaceCnt = 2):
        field_list = [
            f"\n{' '*spaceCnt}double field{field_postfix} = {field_value};",
            f"\n{' '*spaceCnt}float field{field_postfix} = {field_value};",
            f"\n{' '*spaceCnt}int32 field{field_postfix} = {field_value};",
            f"\n{' '*spaceCnt}int64 field{field_postfix} = {field_value};",
            f"\n{' '*spaceCnt}uint32 field{field_postfix} = {field_value};",
            f"\n{' '*spaceCnt}uint64 field{field_postfix} = {field_value};",
            f"\n{' '*spaceCnt}sint32 field{field_postfix} = {field_value};",
            f"\n{' '*spaceCnt}sint64 field{field_postfix} = {field_value};",
            f"\n{' '*spaceCnt}fixed32 field{field_postfix} = {field_value};",
            f"\n{' '*spaceCnt}fixed64 field{field_postfix} = {field_value};",
            f"\n{' '*spaceCnt}sfixed32 field{field_postfix} = {field_value};",
            f"\n{' '*spaceCnt}sfixed64 field{field_postfix} = {field_value};",
            f"\n{' '*spaceCnt}bool field{field_postfix} = {field_value};",
            f"\n{' '*spaceCnt}string field{field_postfix} = {field_value};",
            f"\n{' '*spaceCnt}bytes field{field_postfix} = {field_value};",
            f"\n{' '*spaceCnt}MyEnum{random.randint(1, args.enum[1])} enumField{field_postfix} = {field_value};" 
            if args.enum is not None 
            else f"\n{' '*spaceCnt}int32 field{field_postfix} = {field_value};", 
        ]
        first = second = random.choice(field_list)

        # Add a message field if nested_message is true. Nested message fields will only be in odd index
        # message and will point to some even index message to avoid circular dependency.
        #
        # Messages will be chosen at random from flat field and message field with a 60% probablity for
        # message field
        if args.nested_message and message_count > 1 and (index&1 == 1):
            random_int = random.randint(1, message_count // 2)    
            random_even_number = random_int * 2
            second = f"\n{' '*spaceCnt}Message{random_even_number} field{field_postfix} = {field_value};"
        
        weight = [0.4, 0.6]
        final_choice = random.choices([first, second], weights=weight, k=1)[0]
        
        # Randomly adds repeated fields with a probablity of 35% for reapeated fields
        if args.repeated:
            weight = [0.65, 0.35]
            repeated_choice = "\n" + " "*spaceCnt + "repeated " + final_choice.strip()
            final_choice = random.choices([final_choice, repeated_choice], weights=weight, k=1)[0]
        
        return final_choice

    # Initializing the message
    temp = start

    # Field count
    field = 0

    # Postfix number in the end of each field name in a message (including oneof name)
    field_postfix = 0

    # Value of that field in the message
    field_value = 1

    # Initializing default value
    oneOfCnt = enumCnt = None

    # Resizing enums and oneofs cnts
    if args.enum is not None and args.oneof is not None:
        oneOfCnt = args.oneof[0]
        enumCnt = args.enum[0]
        if oneOfCnt + enumCnt > fields:
            oneOfCnt = min(oneOfCnt, fields//2)
            enumCnt = min(enumCnt, fields//2)

    # Adding oneof to the top in each message
    if args.oneof is not None:
        if not oneOfCnt:
            oneOfCnt = min(args.oneof[0], fields)
        oneOfFieldCnt = args.oneof[1]
        for _ in range(oneOfCnt):
            temp += f"\n  oneof oneofField{field_postfix} {{"
            for _ in range(oneOfFieldCnt):
                field_postfix += 1
                temp += get_random_field(field_postfix, field_value, message_count, 4)
                field_value += 1
            temp += f"\n  }}"
            field += 1
            field_postfix += 1
        
    # Adding enums after oneof
    if args.enum is not None:
        if not enumCnt:
            enumCnt = min(args.enum[0], fields)
        for _ in range(enumCnt):
            final_choice = f"\n  MyEnum{random.randint(1, args.enum[1])} enumField{field_postfix} = {field_value};"
            if args.repeated:
                weight = [0.65, 0.35]
                repeated_choice = "\n  " + "repeated " + final_choice.strip()
                final_choice = random.choices([final_choice, repeated_choice], weights=weight, k=1)[0]
            temp += final_choice
            field_postfix += 1
            field_value += 1
            field += 1
    
    # Adding remaining flat message fields
    while field < fields:
        temp += get_random_field(field_postfix, field_value, message_count)
        field_value += 1
        field += 1
        field_postfix += 1
    
    # Ending the message
    temp += end
    return temp

def generate_service(service_count, rpc_count, message_count):
    temp = ''
    for service in range(1, service_count+1):
        temp += f"\nservice Myservice{service} {{"
        
        # Adds random streaming cases if --streaming is provided
        for rpc in range(1, rpc_count+1):
            temp += f"\n  rpc Method{rpc} ({random.choice(['', 'stream ']) if args.streaming else ''}Message{random.randint(1, message_count)}) returns ({random.choice(['', 'stream ']) if args.streaming else ''}Message{random.randint(1, message_count)});"
        temp += f"\n}}\n"

    return temp

def generate_enum(enum_count, enum_field_count):
    temp = ''
    for enum in range(1, enum_count+1):
        temp += f"\nenum MyEnum{enum} {{"

        for enum_field in range(enum_field_count):
            field_name = "_".join(number_to_words(enum_field).replace('-', "_").strip().split()).upper()
            temp += f"\n  {field_name} = {enum_field};"
        
        temp += f"\n}}\n"
    
    return temp

if __name__ == '__main__':
    outputProtoFileName = 'myProto.proto'
    if args.output is not None:
        outputProtoFileName = args.output
    
    with open(outputProtoFileName, "w") as f:

        # Initial syntax for protofile
        f.write("syntax = \"proto3\";\n")

        # Adding enums to protofile
        if args.enum is not None:
            f.write(generate_enum(args.enum[1], args.enum[2]))

        # Adding services to the protofile
        if args.service is not None:
            f.write(generate_service(args.service[0], args.service[1], args.message_count))

        # Creates atleast 1 message
        for i in range(1,max(2,args.message_count+1)):
            f.write(generate_random_message(args.field_count, i, args.message_count))