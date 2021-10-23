<?php
session_start();

include '../includes/conexao.php';


    if(isset($_POST['btn-editar'])):
        $nome = mysqli_escape_string($con, $_POST['nome']);
        $sobrenome = mysqli_escape_string($con, $_POST['sobrenome']);
        $email = mysqli_escape_string($con, $_POST['email']);
        $idade = mysqli_escape_string($con, $_POST['idade']);

        $id = mysqli_escape_string($con, $_POST['id']);
    
        $sql = "UPDATE cliente SET v_nome_cliente = '$nome', v_sobrenome_cliente = '$sobrenome', v_email_cliente = '$email', i_idade_cliente = '$idade' WHERE i_id_cliente = '$id'";
        if(mysqli_query($con, $sql)): // Se retornou verdadeiro
            echo "<h1><font color = green>--- Atualizado com Sucesso ---</font></h1>";
            ?>
            <meta http-equiv="refresh" content="1;../home.php"></meta>
            <?php
        else:
           echo "<h1><font color = red> Erro ao atualizar :( Voltando...</font></h1>";
            ?>
            <h1><meta http-equiv="refresh" content="1;../home.php"></meta></h1>
            <?php
        endif;
    endif;
?>
