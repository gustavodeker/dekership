<?php
include 'includes/header.php';
include 'includes/conexao.php';
if(isset($_GET['id'])):
    $id = mysqli_escape_string($con, $_GET['id']);
    $sql = "SELECT * FROM cliente WHERE i_id_cliente = '$id'";
    $resultado = mysqli_query($con, $sql);
    $dados = mysqli_fetch_array($resultado);
endif;
?>
<div class="row">
    <div class="col s12 m6 push-m3">
        <h3 class="light">Editar Cliente</h3>
        <form action="php_action/update.php" method="POST">
            <input type="hidden" name='id' value="<?php echo $dados['i_id_cliente'];?>">
            <div class="input-field col s12">
                <input type="text" name="nome" id="nome" value="<?php echo $dados['v_nome_cliente'];?>">
                <label for="nome">Nome</label>
            </div>

            <div class="input-field col s12">
                <input type="text" name="sobrenome" id="sobrenome" value="<?php echo $dados['v_sobrenome_cliente'];?>">
                <label for="sobrenome">Sobrenome</label>
            </div>

            <div class="input-field col s12">
                <input type="text" name="email" id="email" value="<?php echo $dados['v_email_cliente'];?>">
                <label for="email">E-mail</label>
            </div>

            <div class="input-field col s12">
                <input type="text" name="idade" id="idade" value="<?php echo $dados['i_idade_cliente'];?>">
                <label for="idade">Idade</label>
            </div>

            <button type="submit" name="btn-editar" class="btn">Atualizar</button>
            <a href="home.php" type="submit" class="btn green">Voltar</a>
        </form>

    </div>
</div>

<?php include_once 'includes/footer.php';?>