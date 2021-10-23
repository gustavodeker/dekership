<?php
$host = "localhost";
$user = "id17634792_deker";
$senha = "UHut9/bY2#{iSWR#";
$database = "id17634792_sqldeker";

$con = new mysqli($host, $user, $senha, $database);

mysqli_set_charset($con, "utf8");

if($con->connect_errno) {
    dir("Falha na conexão com o banco");
}
?>

