<?php
session_start();

include '../includes/conexao.php';


    if(isset($_POST['id'])):
        
        $id = mysqli_escape_string($con, $_POST['id']);
    
        $sql = "DELETE FROM cliente WHERE i_id_cliente = '$id'";
        if(mysqli_query($con, $sql)): // Se retornou verdadeiro
           header('Location: ../home.php');
        else:
            header('Location: ../home.php');
        endif;
    endif;
?>
