<?php
include 'includes/header.php';
include 'includes/conexao.php';

if(isset($_SESSION['mensagem'])):
   echo $_SESSION['mensagem'];
endif;
?>

<div class="row">
    <div class="col s12 m6 push-m3">
        <h3 class="light"> Clientes</h3>
        <a href="adicionar.php"><button>Adicionar cliente</button></a>
        <table id="clientes">
            <thead>
                <tr>
                    <th class="tb">Nome</th>
                    <th class="tb">Sobrenome</th>
                    <th class="tb">E-mail</th>
                    <th class="tb">Idade</th>
                </tr>
            </thead>
            <tbody>
                <?php
                    $sql = "SELECT * FROM cliente";
                    $resultado = mysqli_query($con, $sql);
                    while($dados = mysqli_fetch_array($resultado)):
                ?>
                <tr>
                    <td class="tb"><?php echo $dados['v_nome_cliente']?></td>
                    <td class="tb"><?php echo $dados['v_sobrenome_cliente']?></td>
                    <td class="tb"><?php echo $dados['v_email_cliente']?></td>
                    <td class="tb"><?php echo $dados['i_idade_cliente']?></td>
                    <td class="bt"><a href="editar.php?id=<?php echo $dados['i_id_cliente'];?>"><button>Editar</button></a></td>

                    <td class="bt"><form action="php_action/delete.php" method="POST">
                        <input type="hidden" name="id" value="<?php echo $dados['i_id_cliente'];?>">
                        <button type="submit" name="btn-deletar">Deletar</button>
                    </form></td>                 
    </div>
  </div>
                </tr>
                <?php endwhile; ?>
            </tbody>
        </table>
    </div>
</div>


<?php include_once 'includes/footer.php';?>