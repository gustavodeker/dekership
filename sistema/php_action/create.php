<?php
session_start();

include '../includes/conexao.php';


    if(isset($_POST['btn-cadastrar'])):
        $nome = mysqli_escape_string($con, $_POST['nome']);
        $sobrenome = mysqli_escape_string($con, $_POST['sobrenome']);
        $email = mysqli_escape_string($con, $_POST['email']);
        $idade = mysqli_escape_string($con, $_POST['idade']);
    
        $sql = "INSERT INTO cliente (v_nome_cliente, v_sobrenome_cliente, v_email_cliente, i_idade_cliente) VALUES ('$nome', '$sobrenome', '$email', '$idade')";

        if(mysqli_query($con, $sql)): // Se retornou verdadeiro
            echo "<h1><font color = green>--- Cadastrado com sucesso! ---</font></h1>";
            ?>
            <meta http-equiv="refresh" content="1;../adicionar.php"></meta>
            <?php
        else:
           echo "<h1><font color = red> Erro ao cadastrar! :( Voltando...</font></h1>";
            ?>
            <h1><meta http-equiv="refresh" content="1;../adicionar.php"></meta></h1>
            <?php
        endif;
    endif;
?>
