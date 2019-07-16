<?php
    // Instructions, argument types
    $instructions = array(
        "add" => array("var", "symb", "symb"),
        "sub" => array("var", "symb", "symb"),
        "mul" => array("var", "symb", "symb"),
        "idiv" => array("var", "symb", "symb"),
        "lt" => array("var", "symb", "symb"),
        "gt" => array("var", "symb", "symb"),
        "eq" => array("var", "symb", "symb"),
        "and" => array("var", "symb", "symb"),
        "or" => array("var", "symb", "symb"),
        "not" => array("var", "symb"),
        "move" => array("var", "symb"),
        "int2char" => array("var", "symb"),
        "stri2int" => array("var", "symb", "symb"),
        "read" => array("var", "type"),
        "write" => array("symb"),
        "concat" => array("var", "symb", "symb"),
        "strlen" => array("var", "symb"),
        "getchar" => array("var", "symb", "symb"),
        "setchar" => array("var", "symb", "symb"),
        "type" => array("var", "symb"),
        "label" => array( "label"),
        "jump" => array( "label"),
        "jumpifeq" => array("label", "symb", "symb"),
        "jumpifneq" => array("label", "symb", "symb"),
        "exit" => array("symb"),
        "dprint" => array("symb"),
        "break" => array(),
        "defvar" => array("var"),
        "call" => array("label"),
        "createframe" => array(),
        "pushframe" => array(),
        "popframe" => array(),
        "return" => array(),
        "pushs" => array("symb"),
        "pops" => array("var")
    );

    // Program parameters for statistics, 1.item => availabe, 2.item => counter value
    $programParams = array(
        "loc" => array(false, 0),
        "comments" => array(false, 0),
        "labels" => array(false, 0),
        "jumps" => array(false, 0),
        "stats" => array(false, "")
    );

    // Increment the given statistics counter
    // @param $type program parameter type
    function incrementCounter($type) {
        global $programParams;
        $programParams[$type][1]++;
    }
   
    // Initialize XML variable, append the default header
    function xmlInit(){
        global $xml;
        $xml->openMemory();
        $xml->setIndent(4);
        $xml->startDocument('1.0', 'UTF-8');
        $xml->startElement('program');
            $xml->writeAttribute('language', 'IPPcode19');
    }

    // Add instruction into the XML variable
    // @param $opcode instruction name
    function xmlAddInstruction($opcode){
        global $order;
        global $xml;

        $xml->startElement('instruction');
        $xml->writeAttribute('order', $order);
        $xml->writeAttribute('opcode', strtoupper($opcode));
    }

    // Add instruction argument into the XML variable.
    // @param $type instruction parameter type
    // @param $text instruction parameter value
    function xmlAddArgument($type, $text){
        global $xml;
        global $paramIndex;
        $argIndex = $paramIndex + 1;

        $arg = "arg" . $argIndex;
        $xml->startElement($arg);
        $xml->writeAttribute('type', $type);
        $xml->text($text);
        $xml->endElement();
    }

    // Check header correctness
    // @param $line first program line
    function checkIppHeader($line) {
        if (strtolower($line[0]) != ".ippcode19" || count($line) != 1) {
            fwrite(STDERR, "ERROR: Wrong header!\n");
            exit(21);
        }
    }

    // Check string format correctness
    // @param $string string to check
    function checkString($string){

        // String starts with a number
        if (ctype_digit(strval($string[0]))){
            fwrite(STDERR, "ERROR: Wrong string format!\n");
            exit(23);
        } else {
            if (preg_match('/(?!\\\\[0-9]{3})[\#\s\\\\]/', $string)){
                fwrite(STDERR, "ERROR: Wrong escape sequence format!\n");
                exit(23);
            }

            // Remove all denied special characters and compare the string with the original string
            $stringWihoutSpecials = preg_replace('/[^a-zA-Z0-9$\\\\&%*!?@:_-]/', '', $string);
            if ($stringWihoutSpecials !== $string) {
                fwrite(STDERR, "ERROR: Wrong string format!\n");
                exit(23);
            }
        }
    }

    // Open the given file and fill it with the variable content
    // @param $programParams allowed program parameters
    // @param $content statistics written to file
    function writeToFile($programParams, $content){
        $fileName = $programParams["stats"][1];
        $statsFound = $programParams["stats"][0];

        if ($statsFound) {
            $file = fopen($fileName, 'w');
            
            if (!$file) {
                fwrite(STDERR, "ERROR: Couldnt't open file\n");
                fclose($file);
                exit(12);
            }

            $fileOK = fwrite($file, $content);

            if (!$fileOK) {
                fwrite(STDERR, "ERROR: Couldn't write to file\n");
                fclose($file);
                exit(12);
            }

            fclose($file);
        } else {
            fwrite(STDERR, "ERROR: Parameter --stats not found\n");
            exit(10);
        }
    }

    // Check each program parameter and make them available
    // @param $arguments program arguments
    // @param $programParams allowed program arguments
    function checkArguments($arguments, $programParams){
        foreach($arguments as &$args){
            switch($args){
                case "--loc":
                    $programParams["loc"][0] = true;
                    break;
                case "--comments":
                    $programParams["comments"][0] = true;
                    break;
                case "--labels":
                    $programParams["labels"][0] = true;
                    break;
                case "--jumps":
                    $programParams["jumps"][0] = true;
                    break;
                case "--help":
                    print( 
                        "\nSkript typu filtr načte ze standardního vstupu zdrojový kód v IPPcode19, " . 
                        "zkontroluje lexikální a syntaktickou správnost kódu a vypíše " .
                        "na standardní výstup XML reprezentaci programu.\n\n");
                    exit(0);
                    break;
                default:
                    $statsAndFile = explode('=', $args, 2);
                    if (count($statsAndFile) == 2 && $statsAndFile[0] == "--stats") {
                        $programParams["stats"][0] = true;
                        $programParams["stats"][1] = $statsAndFile[1];
                    } else {
                        fwrite(STDERR, "ERROR: Wrong program parameter\n");
                        exit(10);
                    }
                    break;
            }
        }
        return $programParams;
    }

    // Fill the variable with statistics counter value in the correct program parameter order
    // @param $arguments program arguments
    // @param $programParams allowed program arguments
    function processStatistics($arguments, $programParams){
        $fileContent;
        foreach($arguments as &$args){
            switch($args){
                case "--loc":
                    if ($programParams["loc"][0]) {
                        $fileContent = $fileContent . $programParams["loc"][1] . "\n";
                    }
                    break;
                case "--comments":
                    if ($programParams["comments"][0]) {
                        $fileContent = $fileContent . $programParams["comments"][1] . "\n";
                    }
                    break;
                case "--labels":
                    if ($programParams["labels"][0]) {
                        $fileContent = $fileContent . $programParams["labels"][1] . "\n";
                    }
                    break;
                case "--jumps":
                    if ($programParams["jumps"][0]) {
                        $fileContent = $fileContent . $programParams["jumps"][1] . "\n";
                    }
                    break;
            }
        }

        writeToFile($programParams, $fileContent);

    }

    // Split instruction parameter into type and name
    // @param $param instruction parameter
    function splitParam($param){
        $frameVar = explode('@', $param, 2);
        
        return $frameVar;
    }

    // Check frame correctness
    // @param $frame variable frame
    function checkFrame($frame){
        if ($frame != "GF" && $frame != "LF" && $frame != "TF") {
            fwrite(STDERR, "ERROR: Wrong parameter!\n");
            exit(23);
        }
    }

    // Compare constant type with the instructions data type
    // @param $type constant type
    // @param $value constant value
    function checkVariableType($type, $value){
        if ($type == "nil") {
            if ($value == "nil") {
                xmlAddArgument("nil", $value);
                return;
            } else {
                fwrite(STDERR, "ERROR: Wrong parameter!\n");
                exit(23);
            }
        }

        $match = false;
        switch ($type) {
            case "int":
                if ($value[0] == '-') {
                    $value = substr($value, 1);
                    if (ctype_digit(strval($value)) || empty($value)) {
                        $match = true;
                        $value = "-" . $value;
                        break;
                    }
                }

                if (ctype_digit(strval($value)) || empty($value)) {
                    $match = true;
                }
                break;
            case "string":
                if (is_string($value)) {
                    checkString($value);
                    $match = true;
                } else if (empty($value)){
                    $match = true;
                }
                break;
            case "bool":
                if ($value == "true" || $value == "false") {
                    $match = true;
                }
                break;
        }

        if ($match) {
            xmlAddArgument($type, $value);
        } else {
            fwrite(STDERR, "ERROR: Wrong parameter!\n");
            exit(23);
        }
    }

    // Decides If the parameter is variable or constant
    // @param $param instruction parameter
    function processVariable($param){
        $split = splitParam($param);
        if (strlen($split[0]) == 2) {
            $frame = $split[0];
            $varName = $split[1];
            checkFrame($frame);
            checkString($varName);
            xmlAddArgument("var", $param);
        } else {
            checkVariableType($split[0], $split[1]);
        }
    }

    // Checks If the parameter format is correct
    // @param $param instruction parameter
    function checkDataTypes($param){
        if (strpos($param, '@') !== false) {
            processVariable($param);
        } else {
            fwrite(STDERR, "ERROR: Wrong parameter!\n");
            exit(23);
        }
    }

    // Checks If label format is valid
    // @param $string label value
    function checkLabel($string){
        if (is_string($string)) {
            if (strpos($string, '@') !== false) {
                fwrite(STDERR, "ERROR: Wrong label format!\n");
                exit(23);
            } else {
                checkString($string);

                xmlAddArgument("label", $string);
            }
        } else {
            fwrite(STDERR, "ERROR: Wrong label format!\n");
            exit(23);
        }
    }

    // Check each instruction parameter type
    // @param $line one program line with instruction and parameters
    // @param $instruction array of allowed instructions
    function processParameters($line, $instructions){
        $lineParamCount = count($line) - 1;
        $instParamCount = count($instructions[$line[0]]);
        $parameters = $instructions[$line[0]];

        global $paramIndex; 
        $paramIndex = 0;
        foreach($parameters as &$dataTypes){
            $param = $line[$paramIndex + 1];

            switch($dataTypes){
                case "var":
                    $frameVar = splitParam($param);
                    $frame = $frameVar[0];
                    $varName = $frameVar[1];
                    
                    checkFrame($frame);
                    checkString($varName);
                    xmlAddArgument("var", $param);
                    break;
                case "symb":
                    checkDataTypes($param);
                    break;
                case "label":
                    checkLabel($param);
                    break;
                case "type":
                    if ($param != "int" && $param != "string" && $param != "bool" && $param != "nil") {
                        fwrite(STDERR, "ERROR: Wronng parameter!\n");
                        exit(23);
                    } else {
                        xmlAddArgument("type", $param);
                    }
                    break;
                default:
                    break;
            }
            $paramIndex++;
        }

    }

    // Increment jumps or labels counter
    // @param $instruction instruction to check
    function checkInstructionStats($instruction){
        switch($instruction){
            case "jump":
            case "jumpifeq":
            case "jumpifneq":
                incrementCounter("jumps");
                break;
            case "label":
                incrementCounter("labels");
                break;
        }
    }

    // Check if the instruction is correct
    // @param $line one program line with instruction and parameters
    // @param $instructions array of allowed instructions
    function processInstruction($line, $instructions) {
        $line[0] = strtolower($line[0]);

        if (array_key_exists($line[0], $instructions)) {
            $lineParamCount = count($line) - 1;
            $instParamCount = count($instructions[$line[0]]);

            if ($lineParamCount != $instParamCount) {
                fwrite(STDERR, "ERROR: Wrong parameters!\n");
                exit(23);
            } else {
                xmlAddInstruction($line[0]);
                checkInstructionStats($line[0]);
                incrementCounter("loc");

                processParameters($line, $instructions);
            }
        } else {
            fwrite(STDERR, "ERROR: Wrong instruction!\n");
            exit(22);
        }

        
    }

    // MAIN

    // Process program parameters
    if ($argc > 1) {
        array_shift($argv);
        $programParams = checkArguments($argv, $programParams);
    } elseif ($argc >= 6) {
        fwrite(STDERR, "ERROR: Wrong argument!\n");
        exit(10);
    }

    // Load from STDIN
    if (!$stdin = stream_get_contents(STDIN)) {
        fwrite(STDERR, "ERROR: Empty input!\n");
        exit(21);
    }

    // Create XML
    $xml = new XMLWriter();
    xmlInit();

    // Convert each line to array
    $stdin = explode("\n", $stdin);

    $paramIndex = 0;
    $order = 1;
    $firstLine = true;
    foreach($stdin as &$line){
        // Remove unnecessary whitespaces
        $line = trim(preg_replace('/\s+/',' ', $line));
        
        // Remove comments
        $commentPos = strpos($line, '#');
        if ($commentPos !== false) {
            $line = substr($line, 0, $commentPos);

            // Increment comment stats
            incrementCounter("comments");
        }

        // Convert each word to array
        $line = explode(" ", $line);

        // Remove empty keys from array
        $line = array_filter($line);

        // Skip empty array
        if (empty($line)) {
            continue;
        }

        // .IPPcode19 header check
        if ($firstLine){
            checkIppHeader($line);
            $firstLine = false;
            continue;
        }

        processInstruction($line, $instructions);
        $xml->endElement();
        $order++;
    }

    // Print out xml
    if (!$firstLine) {
        if ($argc > 1) {
            processStatistics($argv, $programParams);
        }

        $xml->endElement();
        $xml->endDocument();
        echo $xml->outputMemory(TRUE);
    }
?>