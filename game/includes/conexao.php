<?php
$host = "localhost";
$user = "id17775253_deker";
$senha = "UD3suK)u[d9siHv@";
$database = "id17775253_dekership";

$con = mysqli_connect($host, $user, $senha, $database);

if(mysqli_connect_error()):
    echo "Falha na conexão: ".mysqli_connect_error();
endif;
?>