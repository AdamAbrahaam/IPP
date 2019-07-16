import sys
import argparse
import numbers
import re
import copy
import operator
import xml.etree.ElementTree as ET

# Class for frames and methods for frames
class Frames:
    init = False
    variables = {}

    def append(self, varName, init, type, value):
        if self.init:
            self.variables[varName] = {"init": init,
                                        "type": type,
                                        "value": value}
        else:
            terminate("Frame not initialized!", 55)

    def clearFrame(self):
        self.variables.clear()

# Class for stack and methods for stack
class Stack:
    stack = []

    def push(self, frame):
        self.stack.insert(0, frame)

    def pop(self):
        del self.stack[0]

    def top(self):
        return self.stack[0]


# List of avalaible instruction
def getInstructionList():
    instructionList = {
        # Frames, function calls
        "move": {"var": [], "symb1": ["int", "bool", "string"]},
        "createframe": {},
        "pushframe": {},
        "popframe": {},
        "defvar": {"var": []},
        "call": {"label": []},
        "return": {},

        # Data stack
        "pushs": {"symb1": ["int", "bool", "string"]},
        "pops": {"var": []},

        # Operations
        "add": {"var": [], "symb1": ["int"], "symb2": ["int"]},
        "sub": {"var": [], "symb1": ["int"], "symb2": ["int"]},
        "mul": {"var": [], "symb1": ["int"], "symb2": ["int"]},
        "idiv": {"var": [], "symb1": ["int"], "symb2": ["int"]},
        "lt": {"var": [], "symb1": ["int", "bool", "string"], "symb2": ["int", "bool", "string"]},
        "gt": {"var": [], "symb1": ["int", "bool", "string"], "symb2": ["int", "bool", "string"]},
        "eq": {"var": [], "symb1": ["int", "bool", "string"], "symb2": ["int", "bool", "string"]},
        "and": {"var": [], "symb1": ["bool"], "symb2": ["bool"]},
        "or": {"var": [], "symb1": ["bool"], "symb2": ["bool"]},
        "not": {"var": [], "symb1": ["bool"]},
        "int2char": {"var": [], "symb1": ["int"]},
        "stri2int": {"var": [], "symb1": ["string"], "symb2": ["int"]},

        # In-Output
        "read": {"var": [], "type": ["int", "bool", "string"]},
        "write": {"symb1": ["int", "bool", "string"]},

        # Strings
        "concat": {"var": [], "symb1": ["string"], "symb2": ["string"]},
        "strlen": {"var": [], "symb1": ["string"]},
        "getchar": {"var": [], "symb1": ["string"], "symb2": ["int"]},
        "setchar": {"var": [], "symb1": ["int"], "symb2": ["string"]},

        # Types
        "type": {"var": [], "symb1": ["int", "bool", "string"]},

        # Program flow
        "label": {"label": []},
        "jump": {"label": []},
        "jumpifeq": {"label": [], "symb1": ["int", "bool", "string"], "symb2": ["int", "bool", "string"]},
        "jumpifneq": {"label": [], "symb1": ["int", "bool", "string"], "symb2": ["int", "bool", "string"]},
        "exit": {"symb1": ["int"]},

        # Debug
        "dprint": {"symb1": ["int", "bool", "string"]},
        "break": {}
    }

    return instructionList


# print error msg to stderr, exit with the proper error code
def terminate(errorMessage, errorCode):
    print("ERROR: {}".format(errorMessage), file=sys.stderr)
    sys.exit(errorCode)


# inspect root format
def checkRoot(root):
    if root.tag != "program":
        terminate("Wrong XML root format!", 31)

    rootItems = root.items()
    for item in rootItems:
        attribute = item[0]
        attrText = item[1]

        if attribute == "language" and attrText != "IPPcode19":
            terminate("Wrong XML root format!", 31)
        elif attribute != "name" and attribute != "description" and attribute != "language":
            terminate("Wrong XML root format!", 31)


# Check instruction attribute format
def checkInstructionAttributes(attributes):
    if len(attributes) != 2 or len(attributes[0]) != 2 or len(attributes[1]) != 2:
        terminate("Incorrect instruction attribute count!", 31)

    attrOrder = attributes[0][0]
    attrNumber = attributes[0][1]
    attrOpcode = attributes[1][0]

    try:
        attrNumber = float(attrNumber)
    except:
        terminate("Wrong instruction order number!", 31)

    if attrOrder != "order" or not attrNumber.is_integer() or attrOpcode != "opcode":
        terminate("Wrong instruction attribute!", 31)



# Sort instructions by order number
def sortInstructions(instructions):
    insToSort = []
    for i in instructions:
        key = i.items()[0][1]
        insToSort.append((key, i))

    try:
        insToSort.sort()
    except:
        terminate("Wrong order number!", 32)

    instructions[:] = [item[-1] for item in insToSort]
    return instructions


# Check argument attribute format
def checkArgumentAttributes(arguments):
    for arg in arguments:
        argNumber = arg.tag
        if len(argNumber) < 4:
            terminate("Wrong argument attribute format!", 31)

        argFormat = argNumber[:3]
        argNumber = argNumber[3:]
        try:
            argNumber = float(argNumber)
        except:
            terminate("Wrong argument number!", 31)

        if argFormat != "arg" or not argNumber.is_integer() or arg.keys()[0] != "type":
            terminate("Wrong argument attribute!", 31)
        

# Sort arguments 
def sortArguments(arguments):
    argsToSort = []
    for arg in arguments:
        key = arg.tag
        argsToSort.append((key, arg))

    try:
        argsToSort.sort()
    except:
        terminate("Wrong argument order number!", 32)

    arguments[:] = [item[-1] for item in argsToSort]
    return arguments


# Check string format
def checkString(string, isVarOrLabel):
    if isVarOrLabel and string[0].isdigit():
        terminate("Variables and labels can not start with numbers!", 32)

    
    #regexSpecial = re.search(r"^([a-zA-Z]|[_\-$&%*@!?])([\w_\-$&%*@!?])*$", string)

    #if string != stringWithoutSpecial and isVarOrLabel:
        #terminate("Using denied characters in variables or labels!", 32)

    regex = re.search(r"(?!\\[0-9]{3})[\s\\#]", string)                     
    if regex is not None: 
        terminate("Wrong escape sequence format!", 32)


# Check label format
def checkLabel(string):
    if string.find('@') != -1:
        terminate("Wrong label format!", 32)

    if isinstance(string, str):
        checkString(string, True)
    else:
        terminate("Wrong label format!", 32)


# Process variable
def processTypeVar(argValue):
    frameVar = argValue.partition("@")
    if frameVar[1] != "@":
            terminate("Wrong frame format!", 32)
    if frameVar[0] != "GF" and frameVar[0] != "LF" and frameVar[0] != "TF":
            terminate("Wrong frame format!", 32)

    checkString(frameVar[2], True)
    return frameVar



# Check data types
def checkTypeSymb(listArgType, listDataTypes, argType, argValue):
    match = False
    if argType == "var":
        processTypeVar(argValue)
        match = True

    elif argType == "int":
        for type in listDataTypes:
            if type == argType:
                match = True
                            
            if match and argValue:
                try:
                    argValue = float(argValue)
                except:
                    terminate("Argument value is not an integer!", 32)
                
                if not argValue.is_integer():
                    terminate("Wrong integer format!", 32)

                break


    elif argType == "string":
        for type in listDataTypes:
            if type == argType:
                match = True

            if match and argValue:
                checkString(argValue, False)
            
                break

    elif argType == "bool":
        for type in listDataTypes:
            if type == argType:
                if argValue == "true" or argValue == "false":
                    match = True
                else:
                    terminate("Wrong bool argument format!", 32)

            if match:
                break

    elif argType == "nil":
        match = True
        if argValue != "nil":
            terminate("Wrong nil format!", 32)

    else:
        terminate("Wrong symbol format!", 32)

    if not match:
        terminate("Argument does not match!", 32)


# Analyze arguments
def processArguments(listArgType, listDataTypes, argType, argValue):
    if listArgType == "var":
        if listArgType != argType:
            terminate("Wrong attribute type!", 32)

        processTypeVar(argValue)
            
    elif listArgType == "symb1" or listArgType == "symb2":
        checkTypeSymb(listArgType, listDataTypes, argType, argValue)

    elif listArgType == "label":
        if listArgType != argType:
            terminate("Wrong attribute type!", 32)
        
        checkLabel(argValue)

    elif listArgType == "type":
        if listArgType != argType:
            terminate("Wrong attribute type!", 32)

        if argValue != "int" and argValue != "string" and argValue != "bool" and argValue != "nil":
            terminate("Wrong type format!", 32)

    else:
        terminate("Wrong argument type!", 32)




# Process instruction and its arguments
def processInstruction(instruction, arguments, instructionList):
    iListArguments = instructionList.get(instruction)
    try:
        iListArgCount = len(iListArguments)
    except:
        terminate("Instruction not found!", 32)

    argCount = len(arguments)

    if iListArguments is None:
        terminate("Instruction not found!", 32)

    if arguments:
        checkArgumentAttributes(arguments)
        arguments = sortArguments(arguments)
    
    if iListArgCount != argCount:
        terminate("Incorrect number of arguments!", 32)

    for index, listArgType in enumerate(iListArguments):
        listDataTypes = iListArguments[listArgType]     
        argType = arguments[index].items()[0][1]
        argValue = arguments[index].text

        processArguments(listArgType, listDataTypes, argType, argValue)


# Get label positions
def getLabels(instructions):
    labels = {}

    for index, inst in enumerate(instructions):
        opcode = inst.items()[1][1].lower()
        arguments = list(inst)
        
        if opcode == "label":
            if arguments[0].text in labels:
                terminate("Label already exists!", 52)
            else:
                labels[arguments[0].text] = { "index": index }
            
    return labels


# Return a list of symbol values
def getSymbValues(arguments, argNum, GF, TF, LF):
    if arguments[argNum].text is None:
        symbInit = True
        symbType = arguments[argNum].items()[0][1]
        symbValue = ""
    elif arguments[argNum].text.find("@") != -1:
        frame = arguments[argNum].text[:2]
        var = arguments[argNum].text[3:]

        if frame == "GF" or frame == "LF" or frame == "TF":
            if eval(frame).init:
                try:
                    symb = eval(frame).variables.get(var).copy()
                except:
                    terminate("Variable not found in the frame!", 54)
                
                symbInit = symb.get("init")
                symbType = symb.get("type")
                symbValue = symb.get("value")
            else:
                terminate("Frame is not initialized!", 55)
        else:
            symbInit = True
            symbType = arguments[argNum].items()[0][1]
            symbValue = arguments[argNum].text
    else:
        symbInit = True
        symbType = arguments[argNum].items()[0][1]
        symbValue = arguments[argNum].text

    return [symbInit, symbType, symbValue]


# Assign type, value to var
def assignToVar(arguments, symbValues, GF, TF, LF):
    frameVar = processTypeVar(arguments[0].text)
    frame = frameVar[0]
    var = frameVar[2]

    symbInit = symbValues[0]
    symbType = symbValues[1]
    symbValue = symbValues[2]
    if eval(frame).init:
        if var in eval(frame).variables:
            eval(frame).variables[var]["init"] = symbInit
            eval(frame).variables[var]["type"] = symbType
            eval(frame).variables[var]["value"] = symbValue
        else:
            terminate("Variable not found in the frame!", 54)
    else:
        terminate("Frame not initialized!", 55)


# Basic arithmetic operations
def executeArithmetic(symbType, symbValue, symbValue2, op):
    if symbType == "int":
        symbValue = int(symbValue)
        symbValue2 = int(symbValue2)
    elif symbType == "bool":
        symbValue = bool(symbValue)
        symbValue2 = bool(symbValue2)

    return op(symbValue, symbValue2)


# Execute instructions
def executeInstructions(instructions, GF, TF, LF, stack, inputFile):
    index = 0

    labels = getLabels(instructions)
    dataStack = []
    returnIndex = None

    while index < len(instructions):
        opcode = instructions[index].items()[1][1]
        opcode = opcode.lower()
        arguments = list(instructions[index])
        arguments = sortArguments(arguments)

        if opcode == "defvar":
            frameVar = processTypeVar(arguments[0].text)
            frame = frameVar[0]
            var = frameVar[2]

            eval(frame).append(var, False, "", "")

        elif opcode == "createframe":
            if TF.init:
                TF.clearFrame()

            TF.init = True

        elif opcode == "pushframe":
            if TF.init:
                LF.init = True
                LF.variables = TF.variables.copy()
                stack.push(copy.copy(LF))
                TF.init = False
                TF.clearFrame()
            else:
                terminate("Frame not initialized!", 55)

        elif opcode == "popframe":
            if TF.init:
                if stack.stack:
                    TF.variables = eval(stack.top()).variables.copy()
                    stack.pop()
                    LF.clearFrame()
                    LF.init = False
                else:
                    terminate("Stack is empty!", 55)
            else:
                terminate("Temp. frame does not exist!", 55)

        elif opcode == "move":
            symbValues = getSymbValues(arguments, 1, GF, TF, LF)

            assignToVar(arguments, symbValues, GF, TF, LF)

        elif opcode == "call":
            if arguments[0].text in labels:
                returnIndex = index
                index = labels[arguments[0].text]["index"] - 1
            else:
                terminate("Label does not exist!", 52)
            
        elif opcode == "return":
            if returnIndex is None:
                terminate("No return value!", 52)
            else:
                index = returnIndex
                returnIndex = None

        elif opcode == "pushs":
            symbValues = getSymbValues(arguments, 0, GF, TF, LF)
            symbType = symbValues[1]
            symbValue = symbValues[2]

            dataStack.insert(0, {"type": symbType, "value": symbValue})

        elif opcode == "pops":
            if dataStack:
                stackTop = dataStack[0].copy()
                del dataStack[0]

                symbValues = [True, stackTop["type"], stackTop["value"]]
                assignToVar(arguments, symbValues, GF, TF, LF)
            else:
                terminate("Data stack is empty!", 56)

        elif opcode == "add":
            symbValues = getSymbValues(arguments, 1, GF, TF, LF)
            symbValue = symbValues[2]
            symbType = symbValues[1]

            symbValues = getSymbValues(arguments, 2, GF, TF, LF)
            symbValue2 = symbValues[2]
            symbType2 = symbValues[1]

            if symbValue == "" or symbValue2 == "":
                terminate("Variable is empty!", 56)
                
            if symbType != symbType2:
                terminate("Not matching operand types!", 53)

            if symbType == "nil" or symbType2 == "nil":
                terminate("Wrong operand!", 53)

            result = executeArithmetic(symbType, symbValue, symbValue2, operator.add)

            symbValues = [True, "int", result]
            assignToVar(arguments, symbValues, GF, TF, LF)

        elif opcode == "sub":
            symbValues = getSymbValues(arguments, 1, GF, TF, LF)
            symbValue = symbValues[2]
            symbType = symbValues[1]

            symbValues = getSymbValues(arguments, 2, GF, TF, LF)
            symbValue2 = symbValues[2]
            symbType2 = symbValues[1]

            if symbValue == "" or symbValue2 == "":
                terminate("Variable is empty!", 56)
                
            if symbType != symbType2:
                terminate("Not matching operand types!", 53)

            if symbType == "nil" or symbType2 == "nil":
                terminate("Wrong operand!", 53)

            result = executeArithmetic(symbType, symbValue, symbValue2, operator.sub)

            symbValues = [True, "int", result]
            assignToVar(arguments, symbValues, GF, TF, LF)

        elif opcode == "mul":
            symbValues = getSymbValues(arguments, 1, GF, TF, LF)
            symbValue = symbValues[2]
            symbType = symbValues[1]

            symbValues = getSymbValues(arguments, 2, GF, TF, LF)
            symbValue2 = symbValues[2]
            symbType2 = symbValues[1]

            if symbValue == "" or symbValue2 == "":
                terminate("Variable is empty!", 56)
                
            if symbType != symbType2:
                terminate("Not matching operand types!", 53)

            if symbType == "nil" or symbType2 == "nil":
                terminate("Wrong operand!", 53)

            result = executeArithmetic(symbType, symbValue, symbValue2, operator.mul)

            symbValues = [True, "int", result]
            assignToVar(arguments, symbValues, GF, TF, LF)

        elif opcode == "idiv":
            symbValues = getSymbValues(arguments, 1, GF, TF, LF)
            symbValue = symbValues[2]
            symbType = symbValues[1]

            symbValues = getSymbValues(arguments, 2, GF, TF, LF)
            symbValue2 = symbValues[2]
            symbType2 = symbValues[1]

            if symbValue == "" or symbValue2 == "":
                terminate("Variable is empty!", 56)
                
            if symbType != symbType2:
                terminate("Not matching operand types!", 53)

            if symbType == "nil" or symbType2 == "nil":
                terminate("Wrong operand!", 53)

            if symbValue2 == "0":
                terminate("Division by zero!", 57)

            result = executeArithmetic(symbType, symbValue, symbValue2, operator.floordiv)

            symbValues = [True, "int", result]
            assignToVar(arguments, symbValues, GF, TF, LF)

        elif opcode == "lt":
            symbValues = getSymbValues(arguments, 1, GF, TF, LF)
            symbValue = symbValues[2]
            symbType = symbValues[1]

            symbValues = getSymbValues(arguments, 2, GF, TF, LF)
            symbValue2 = symbValues[2]
            symbType2 = symbValues[1]

            if symbValue == "" or symbValue2 == "":
                terminate("Variable is empty!", 56)

            if symbType != symbType2:
                terminate("Not matching operand types!", 53)

            if symbType == "nil" or symbType2 == "nil":
                terminate("Wrong operand!", 53)

            result = executeArithmetic(symbType, symbValue, symbValue2, operator.lt)

            symbValues = [True, "bool", result]
            assignToVar(arguments, symbValues, GF, TF, LF)

        elif opcode == "gt":
            symbValues = getSymbValues(arguments, 1, GF, TF, LF)
            symbValue = symbValues[2]
            symbType = symbValues[1]

            symbValues = getSymbValues(arguments, 2, GF, TF, LF)
            symbValue2 = symbValues[2]
            symbType2 = symbValues[1]

            if symbValue == "" or symbValue2 == "":
                terminate("Variable is empty!", 56)
                
            if symbType != symbType2:
                terminate("Not matching operand types!", 53)

            if symbType == "nil" or symbType2 == "nil":
                terminate("Wrong operand!", 53)

            result = executeArithmetic(symbType, symbValue, symbValue2, operator.gt)

            symbValues = [True, "bool", result]
            assignToVar(arguments, symbValues, GF, TF, LF)

        elif opcode == "eq":
            symbValues = getSymbValues(arguments, 1, GF, TF, LF)
            symbValue = symbValues[2]
            symbType = symbValues[1]

            symbValues = getSymbValues(arguments, 2, GF, TF, LF)
            symbValue2 = symbValues[2]
            symbType2 = symbValues[1]

            if symbValue == "" or symbValue2 == "":
                terminate("Variable is empty!", 56)
                
            if symbType != symbType2:
                terminate("Not matching operand types!", 53)

            if symbType == "nil" and symbType2 == "nil":
                symbValues = [True, "bool", True]
            else:
                result = executeArithmetic(symbType, symbValue, symbValue2, operator.eq)
                symbValues = [True, "bool", result]

            assignToVar(arguments, symbValues, GF, TF, LF)

        elif opcode == "and":
            symbValues = getSymbValues(arguments, 1, GF, TF, LF)
            symbValue = symbValues[2]
            symbType = symbValues[1]

            symbValues = getSymbValues(arguments, 2, GF, TF, LF)
            symbValue2 = symbValues[2]
            symbType2 = symbValues[1]

            if symbValue == "" or symbValue2 == "":
                terminate("Variable is empty!", 56)
                
            if symbType != symbType2:
                terminate("Not matching operand types!", 53)

            if symbType == "nil" or symbType2 == "nil":
                terminate("Wrong operand!", 53)

            result = executeArithmetic(symbType, symbValue, symbValue2, operator.and_)

            symbValues = [True, "bool", result]
            assignToVar(arguments, symbValues, GF, TF, LF)

        elif opcode == "or":
            symbValues = getSymbValues(arguments, 1, GF, TF, LF)
            symbValue = symbValues[2]
            symbType = symbValues[1]

            symbValues = getSymbValues(arguments, 2, GF, TF, LF)
            symbValue2 = symbValues[2]
            symbType2 = symbValues[1]

            if symbValue == "" or symbValue2 == "":
                terminate("Variable is empty!", 56)
                
            if symbType != symbType2:
                terminate("Not matching operand types!", 53)

            if symbType == "nil" or symbType2 == "nil":
                terminate("Wrong operand!", 53)

            result = executeArithmetic(symbType, symbValue, symbValue2, operator.or_)

            symbValues = [True, "bool", result]
            assignToVar(arguments, symbValues, GF, TF, LF)

        elif opcode == "not":
            symbValues = getSymbValues(arguments, 1, GF, TF, LF)
            symbValue = symbValues[2]
            symbType = symbValues[1]

            if symbValue == "":
                terminate("Variable is empty!", 56)

            if symbType == "nil":
                terminate("Wrong operand!", 53)

            if symbValue == "true":
                result = "false"
            elif symbValue == "false":
                result = "true"

            symbValues = [True, "bool", result]
            assignToVar(arguments, symbValues, GF, TF, LF)

        elif opcode == "int2char":
            symbValues = getSymbValues(arguments, 1, GF, TF, LF)
            symbValue = symbValues[2]
            symbType = symbValues[1]

            if symbValue == "":
                terminate("Variable is empty!", 56)

            if symbType == "nil":
                terminate("Wrong operand!", 53)

            try:
                result = chr(symbValue)
            except:
                terminate("Value is out of range!", 58)

            symbValues = [True, "string", result]
            assignToVar(arguments, symbValues, GF, TF, LF)
            
        elif opcode == "stri2int":
            symbValues = getSymbValues(arguments, 1, GF, TF, LF)
            symbValue = symbValues[2]
            symbType = symbValues[1]
            
            symbValues = getSymbValues(arguments, 2, GF, TF, LF)
            symbValue2 = symbValues[2]
            symbType2 = symbValues[1]

            if symbValue == "" or symbValue2 == "":
                terminate("Variable is empty!", 56)

            if symbType == "nil" or symbType2 == "":
                terminate("Wrong operand!", 53)

            try:
                result = ord(symbValue[int(symbValue2)])
            except:
                terminate("Value out of range!", 58)

            symbValues = [True, "int", result]
            assignToVar(arguments, symbValues, GF, TF, LF)

        elif opcode == "read":
            symbValues = getSymbValues(arguments, 1, GF, TF, LF)
            symbValue = symbValues[2]

            if inputFile:
                with open(inputFile.name) as f:
                    result = f.readline()
            else:
                result = input()

            if symbValue == "int":
                try:
                    result = int(result)
                    symbValues = [True, "int", result]
                    assignToVar(arguments, symbValues, GF, TF, LF)
                except:
                    symbValues = [True, "int", 0]
                    assignToVar(arguments, symbValues, GF, TF, LF)

            elif symbValue == "string":
                try:
                    result = str(result)
                    symbValues = [True, "string", result]
                    assignToVar(arguments, symbValues, GF, TF, LF)
                except:
                    symbValues = [True, "string", ""]
                    assignToVar(arguments, symbValues, GF, TF, LF)
                
            elif symbValue == "bool":
                try:
                    result = result.lower()
                    if result == "true":
                        symbValues = [True, "bool", result]
                    else:
                        symbValues = [True, "bool", "false"]
                    
                    assignToVar(arguments, symbValues, GF, TF, LF)
                except:
                    symbValues = [True, "bool", "false"]
                    assignToVar(arguments, symbValues, GF, TF, LF)
        
        elif opcode == "write":
            symbValues = getSymbValues(arguments, 0, GF, TF, LF)
            symbValue = symbValues[2]
            symbType = symbValues[1]

            if symbType == "bool":
                if symbValue == "true":
                    print(True, end='')
                elif symbValue == "false":
                    print(False, end='')
            else:
                print(symbValue, end='')

        elif opcode == "concat":
            symbValues = getSymbValues(arguments, 1, GF, TF, LF)
            symbValue = symbValues[2]
            symbType = symbValues[1]

            symbValues = getSymbValues(arguments, 2, GF, TF, LF)
            symbValue2 = symbValues[2]
            symbType2 = symbValues[1]

            if symbType != "string" or symbType2 != "string":
                terminate("Wrong operand type!", 53)

            result = symbValue + symbValue2

            symbValues = [True, "string", result]
            assignToVar(arguments, symbValues, GF, TF, LF)

        elif opcode == "strlen":
            symbValues = getSymbValues(arguments, 1, GF, TF, LF)
            symbValue = symbValues[2]
            symbType = symbValues[1]

            if symbType != "string":
                terminate("Wrong operand type!", 53)

            result = len(symbValue)
            symbValues = [True, "int", result]
            assignToVar(arguments, symbValues, GF, TF, LF)

        elif opcode == "getchar":
            symbValues = getSymbValues(arguments, 1, GF, TF, LF)
            symbValue = symbValues[2]
            symbType = symbValues[1]

            symbValues = getSymbValues(arguments, 2, GF, TF, LF)
            symbValue2 = symbValues[2]
            symbType2 = symbValues[1]

            if symbType != "string" or symbType2 != "int":
                terminate("Wrong operand type!", 53)

            try:
                result = symbValue[int(symbValue2)]
            except:
                terminate("Value out of range!", 58)
            
            symbValues = [True, "string", result]
            assignToVar(arguments, symbValues, GF, TF, LF)

        elif opcode == "setchar":
            frameVar = processTypeVar(arguments[0].text)
            frame = frameVar[0]
            var = frameVar[2]

            if eval(frame).init:
                try:
                    symb = eval(frame).variables.get(var).copy()
                except:
                    terminate("Variable not found in the frame!", 54)
                
                varType = symb.get("type")
                varValue = symb.get("value")
            else:
                terminate("Frame is not initialized!", 55)

            symbValues = getSymbValues(arguments, 1, GF, TF, LF)
            symbValue = symbValues[2]
            symbType = symbValues[1]

            symbValues = getSymbValues(arguments, 2, GF, TF, LF)
            symbValue2 = symbValues[2]
            symbType2 = symbValues[1]

            if varType != "string" or symbType != "int" or symbType2 != "string":
                terminate("Wrong operand type!", 53)

            if symbValue2 == "":
                terminate("Empty string!", 58)

            try:
                varValue = list(varValue)
                varValue[int(symbValue)] = symbValue2[0]
                varValue = ''.join(varValue)
            except:
                terminate("Value out of range!", 58)

            symbValues = [True, "string", varValue]
            assignToVar(arguments, symbValues, GF, TF, LF)

        elif opcode == "type":
            symbValues = getSymbValues(arguments, 1, GF, TF, LF)
            symbType = symbValues[1]

            result = symbType
            symbValues = [True, "string", result]
            assignToVar(arguments, symbValues, GF, TF, LF)

        elif opcode == "jump":
            if arguments[0].text in labels:
                index = labels[arguments[0].text]["index"] - 1
            else:
                terminate("Label does not exist!", 52)

        elif opcode == "jumpifeq":
            symbValues = getSymbValues(arguments, 1, GF, TF, LF)
            symbValue = symbValues[2]
            symbType = symbValues[1]

            symbValues = getSymbValues(arguments, 2, GF, TF, LF)
            symbValue2 = symbValues[2]
            symbType2 = symbValues[1]

            if symbType != symbType2:
                terminate("Types not match!", 53)

            if symbValue == symbValue2:
                if arguments[0].text in labels:
                    index = labels[arguments[0].text]["index"] - 1
                else:
                    terminate("Label does not exist!", 52)

        elif opcode == "jumpifneq":
            symbValues = getSymbValues(arguments, 1, GF, TF, LF)
            symbValue = symbValues[2]
            symbType = symbValues[1]

            symbValues = getSymbValues(arguments, 2, GF, TF, LF)
            symbValue2 = symbValues[2]
            symbType2 = symbValues[1]

            if symbType != symbType2:
                terminate("Types not match!", 53)

            if symbValue != symbValue2:
                if arguments[0].text in labels:
                    index = labels[arguments[0].text]["index"] - 1
                else:
                    terminate("Label does not exist!", 52)

        elif opcode == "exit":
            symbValues = getSymbValues(arguments, 0, GF, TF, LF)
            symbValue = symbValues[2]
            symbType = symbValues[1]

            if symbType != "int":
                terminate("Wrong operand type!", 53)

            symbValue = int(symbValue)
            if symbValue < 0 or symbValue > 49:
                terminate("Value out of range!", 57)

            sys.exit(symbValue)
        
        elif opcode == "dprint":
            symbValues = getSymbValues(arguments, 0, GF, TF, LF)
            symbValue = symbValues[2]

            print(symbValue, file=sys.stderr)

        elif opcode == "break":
            print("Currently processing instruction number: {}".format(index+1), file=sys.stderr)

        index = index + 1

        
# Prepare instructions for processing
def prepareInstructions(xmlTree, GF, TF, LF, stack, inputFile):
    instructions = xmlTree.findall("instruction")
    instructions = sortInstructions(instructions)

    instructionList = getInstructionList()

    index = 0
    while index < len(instructions):
        checkInstructionAttributes(instructions[index].items())

        opcode = instructions[index].items()[1][1]
        opcode = opcode.lower()
        arguments = list(instructions[index])
        processInstruction(opcode, arguments, instructionList)

        index = index + 1

    executeInstructions(instructions, GF, TF, LF, stack, inputFile)



############################################### MAIN ###############################################
def main():

    if len(sys.argv) <= 1:
        terminate("Wrong number of arguments!", 10)

    if sys.argv[1] == "--help" or sys.argv[1] == "-h":
        print("Use arguments --source and --input!")
        sys.exit(0)

    # parse program arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', help = "XML file", type = argparse.FileType('r'))
    parser.add_argument('--input', help = "XML file", type = argparse.FileType('r'))

    try:
        args = parser.parse_args()
    except:
        sys.exit(10)
        
    sourceFile = args.source
    inputFile = args.input

    # choose between stdin and file
    if sourceFile:
        parseSource = sourceFile
    else:
        parseSource = sys.stdin
    
    if inputFile is None:
        inputFile = sys.stdin

    # parse XML
    try:
        xmlTree = ET.parse(parseSource)
    except:
        terminate("Wrong XML format!", 31)

    # check if root exists
    xmlRoot = xmlTree.getroot()
    if xmlRoot:
        checkRoot(xmlRoot)
    else:
        terminate("XML Root not found", 31)

    # create frames and stack
    stack = Stack()
    GF = Frames()
    LF = Frames()
    TF = Frames()

    GF.init = True 
    stack.push("GF")
  

    # process instructions from XML
    prepareInstructions(xmlTree, GF, TF, LF, stack, inputFile)




if __name__ == "__main__": 
  
    # calling main function 
    main()
