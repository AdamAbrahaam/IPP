<?php
    $recursive = false;
    $dir = getcwd();
    $dir = $dir . '/';
    $parseFile = './parse.php';
    $interpretFile = './interpret.py';
    $intOnly = false;
    $parseOnly = false;
    $filesToTest = [];
    $dirList = [];
    $html = [];

    // Check argument combination validity
    checkArguments();

    // Search for tests
    search($dir, $recursive, $filesToTest);

    // Generate html head and end
    $html = generateHtml($html);
    
    // Execute tests
    $html['body'] = testFiles($filesToTest, $parseOnly, $intOnly, $parseFile, $interpretFile);

    // Combina html parts to final html
    $htmlFinal = $html['start'].$html['body'].$html['end'];

    // Print out html result
    unlink("./tmp");
    echo($htmlFinal);



    function testFiles($filesToTest, $parseOnly, $intOnly, $parseFile, $interpretFile){
        $htmlBody = "";
        $htmlTable = "";
        $success = 0;
        $testCount = 0;
        $allTests = 0;

        foreach($filesToTest as $fileDir=>$filesInDir){
            foreach($filesInDir as $file){
                $passed = false;
                $testCount++;
                $rcVal = fgets(fopen($fileDir.$file.".rc", 'r'));
                touch("./tmp");

                $inFile = $fileDir.$file.".in";
                $outFile = $fileDir.$file.".out";
                $srcFile = $fileDir.$file.".src";
                $trash;
                if($parseOnly){
                    exec("php7.3 ".$parseFile." < ".$srcFile." > ./tmp", $trash, $returnVal);
                    if ($returnVal == 0){
                        if($rcVal == 0){
                            exec("java -jar /pub/courses/ipp/jexamxml/jexamxml.jar ".$outFile." ./tmp", $returnVal);
                            if ($returnVal == 0){
                                $passed = true;
                                $success++;
                            } 
                        }
                    } elseif ($returnVal == $rcVal){
                        $passed = true;
                        $success++;
                    }
                } elseif ($intOnly){
                    exec("python3.6 ".$interpretFile." --source=".$srcFile." --input=".$inFile." > ./tmp", $trash, $returnVal);
                    if ($returnVal == 0){
                        if($rcVal == 0){
                            exec("diff ".$outFile." ./tmp", $returnVal);
                            if (empty($returnVal)){
                                $passed = true;
                                $success++;
                            } 
                        }
                    } elseif ($returnVal == $rcVal){
                        $passed = true;
                        $success++;
                    }
                } else {
                    exec("php7.3 ".$parseFile." < ".$srcFile." > ./tmp", $trash, $returnVal);
                    exec("python3.6 ".$interpretFile." --source=./tmp --input=".$inFile." > ./tmp", $trash, $returnVal);
                    if ($returnVal == 0){
                        if($rcVal == 0){
                            exec("diff ".$outFile." ./tmp", $returnVal);
                            if (empty($returnVal)){
                                $passed = true;
                                $success++;
                            } 
                        }
                    } elseif ($returnVal == $rcVal){
                        $passed = true;
                        $success++;
                    }
                }
                $allTests = $testCount;
                $htmlTable = $htmlTable."
                    <tr>
                        <td>".$testCount."</td>
                        <td>".$file."</td>
                        <td ";
                if($passed){
                    $htmlTable = $htmlTable."style=\"color:green\"> SUCCEEDED";
                }else{
                    $htmlTable = $htmlTable."style=\"color:red\"> FAILED";
                }
                
                $htmlTable = $htmlTable."
                        </td>
                    </tr>
                ";
            };
        };

        $percentage = ($success/$allTests)*100;
        $htmlBody = "
            <p>Number of tests: ".$allTests."</p>
            <p>Successful tests: ".$success." ( ".$percentage." % )</p>
        " . $htmlTable;

        return $htmlBody;

    }

    function generateHtml($html){
        $html['start'] ="
            <!doctype html>
                <html lang=\"en\">
                
                <head>
                    <meta charset=\"utf-8\">
                    <title>IPPcode19 Test</title>
                    <meta name=\"description\" content=\"Test results for IPPcode19 test script\">
                    <meta name=\"author\" content=\"Adam Abraham <xabrah04>\">
                </head>
                <style>
                    .content {
                        text-align: center;
                        max-width: 800px;
                        margin: auto;
                        background: white;
                        padding: 10px;
                    }

                    p {
                        text-align: left;
                        font-size: 20px;
                        font-weight: bold;
                    }

                    table, th, td{
                        border: 1px solid black;
                    }

                    th, td {
                        text-align: center;
                    }
                    th {
                        font-size: 24px;
                    }
                    td {
                        font-size: 20px;
                    }
                </style>
                <body>
                    <div class=\"content\">
                        <h1>IPPcode19 Test Summary</h1>
                        <br>

                        <table style=\"width:100%\">
                            <tr>
                                <th>Number</th>
                                <th>Test name</th> 
                                <th>Result</th>
                            </tr>
            ";

        $html['end'] = "
                        </table>
                    </div>
                </body>
            </html>
        ";

        return $html;
                

    }

    function search($dir, $recursive){
        global $dirList;
        global $filesToTest;

        $Directory = new RecursiveDirectoryIterator($dir);

        if ($recursive){
            $Iterator = new RecursiveIteratorIterator($Directory);
        } else {
            $Iterator = new IteratorIterator($Directory);
        }

        foreach($Iterator as $i){
            $fileExtension = pathinfo($i->getFilename(), PATHINFO_EXTENSION);

            if ($fileExtension == "src") {
                $fileName = pathinfo($i->getFilename(), PATHINFO_FILENAME);
                $fileDir = getDir(realpath($i));
                
                if (!file_exists($fileDir . $fileName . '.in')) {
                    file_put_contents($fileDir . $fileName . '.in', "");
                }
                
                if (!file_exists($fileDir . $fileName . '.out')) {
                    file_put_contents($fileDir . $fileName . '.out', "");
                }
                
                if (!file_exists($fileDir . $fileName . '.rc')) {
                    file_put_contents($fileDir . $fileName . '.rc', "0");
                }

                if (!in_array($fileDir, $dirList)){
                    $dirList[] = $fileDir;
                }

                $filesToTest[$fileDir][$fileName] = $fileName;
            }
        }
        array_multisort($filesToTest, SORT_ASC);
        sort($dirList);
    }
    
    function getDir($path){
        return preg_replace('/^(.*\/).+\.(in|out|rc|src)$/','\1', $path);
    }
    function terminate($errMsg, $errCode){
        fprintf(STDERR, $errMsg);
        exit($errCode);
    }

    function checkArguments(){
        $opts = getopt("", ["help", "directory:", "recursive", "parse-script:", "int-script:", "parse-only", "int-only"]);

        global $argc;
        global $argv;
        global $recursive;
        global $parseFile;
        global $interpretFile;
        global $intOnly;
        global $parseOnly;

        $arguments = 0;

        if ($argc == 1) {
            if (!file_exists('./parse.php')) {
                terminate("File not found!\n", 10);
            }

            if (!file_exists('./interpret.py') ) {
                terminate("File not found!\n", 10);
            }
        } elseif ($argc > 1 && $argc < 8) {
            if (array_key_exists('help', $opts)) {
                print("Validne parametry skriptu:\n\n--directory=path\n--recursive\n--parse-script=file\n--int-script=file\n--parse-only\n--int-only\n");
                exit(0);
            }

            if (array_key_exists('int-only', $opts)) {
                $arguments++;
                $intOnly = true;
            }

            if (array_key_exists('parse-only', $opts)) {
                $arguments++;
                $parseOnly = true;
            }

            if (array_key_exists('directory', $opts)) {
                $lastChar = substr($opts['directory'], -1);
                if ($lastChar != '/'){
                    $opts['directory'] = $opts['directory'] . '/';
                }
                $dir = $opts['directory'];
                if (!file_exists($dir)){
                    terminate("Directory not found!\n", 10);
                }
                $arguments++;
            }

            if (array_key_exists('recursive', $opts)) {
                $recursive = true;
                $arguments++;
            }

            if (array_key_exists('parse-script', $opts)) {
                if ($intOnly){
                    terminate("Wrong argument combination!\n", 10);
                }
                $parseFile = $opts['parse-script'];
                if (!file_exists($parseFile)){
                    terminate("File not found!\n", 10);
                }
                $arguments++;
            }

            if (array_key_exists('int-script', $opts)) {
                if ($parseOnly){
                    terminate("Wrong argument combination!\n", 10);
                }
                $interpretFile = $opts['int-script'];
                if (!file_exists($interpretFile)){
                    terminate("File not found!\n", 10);
                }
                $arguments++;
            }

            if ($arguments != ($argc - 1)){
                terminate("Invalid argument!\n", 10);
            }
        } else {
            terminate("Wrong argument combination!\n", 10);
        }
    }
?>