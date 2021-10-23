<?php
require 'conexao.php';
session_start();
##
// Botão enviar
if(isset($_POST['btn_entrar'])):
    $erros = array();
    $nickname = mysqli_escape_string($con,$_POST['nickname']);
    $senha = mysqli_escape_string($con,$_POST['senha']);
    if(empty($nickname) or empty($senha)):
        $erros[] = "<li> Campos obrigatórios </li>";
    else:
        $sql = "SELECT nickname FROM gplayers WHERE nickname = '$nickname'";
        $resultado = mysqli_query($con, $sql);

        if(mysqli_num_rows($resultado) > 0):
            $sql = "SELECT * FROM gplayers WHERE nickname = '$nickname' AND senha = '$senha'";
            $resultado = mysqli_query($con, $sql);

            if(mysqli_num_rows($resultado) == 1):
                $dados = mysqli_fetch_array($resultado); // converter o resultado em array para variavel dados
                $_SESSION['logado'] = true;
                $_SESSION['id'] = $dados['id'];
                header('Location: game.php');
            else:
                $erros[] = "<li> Dados incorretos </li>"; # nickname ou senha incorretos
                
            endif;
        else:
            $erros[] = "<li> Dados incorretos </li>"; # nickname incorreto
        endif;
    endif;
endif;
?>