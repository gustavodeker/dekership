<?php
session_start();
date_default_timezone_set('America/Sao_Paulo');

$servidor = "191.252.38.111";
$usuario = "externo";
$senha = "Sistema@123";
$banco = "dekership";

try {
    $pdo = new PDO("mysql:host=$servidor;port=3333;dbname=$banco;charset=utf8", $usuario, $senha);
    $pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
    //echo "Conectado";
} catch (PDOException $erro) {
    echo "Falha ao conectar." . $erro;
}

function cadastro()
{
    global $pdo;
    //Receber e limpar dados do post
    $usuario = limpaPost(strtolower($_POST['usuario']));
    $email = limpaPost($_POST['email']);
    $senha = limpaPost($_POST['senha']);
    $senha_cript = password_hash($senha, PASSWORD_ARGON2ID);

    //Verificação individual de campos
    //login
    if (!preg_match('/^[A-Za-z0-9-]+$/', $usuario)) {
        $_SESSION['mensagemerro'] = "Apenas letras e números no usuário!";
    }
    //Senha
    if (strlen($senha) < 6) {
        $_SESSION['mensagemerro'] = "Senha deve ter 6 caracteres ou mais!";
    }

    if (!isset($_SESSION['mensagemerro'])) {
        //Verificar se o usuário já está cadastrado
        $sql = $pdo->prepare("SELECT * FROM usuario WHERE usuario=? or email=? ");
        $sql->execute(array($usuario, $email));
        $user = $sql->fetch();

        $data = date('Y-m-d H:i:s');

        if (!$user) {
            try {
                $sql = $pdo->prepare("INSERT INTO usuario VALUES (null,?,?,?, null, ?)");
                $sql->execute(array($usuario, $email, $senha_cript, $data));
                $_SESSION['mensagem'] = "Cadastrado com sucesso !";
            } catch (PDOException $erro) {
                echo "ERRO::: " . $erro;
            }
        } else {
            $_SESSION['mensagemerro'] = "Usuário ou email já cadastrados!";
        }
    }
}

function verificaLogin()
{
    global $pdo;
    //Receber os dados vindos do post e limpar
    $name = limpaPost(strtolower($_POST['usuario']));
    $senha = limpaPost($_POST['senha']);

    //Verificar se existe o usuário no banco
    $sql = $pdo->prepare("SELECT * FROM usuario WHERE usuario =? LIMIT 1");
    $sql->execute(array($name));
    $usuario = $sql->fetch(PDO::FETCH_ASSOC); //Para vir como matriz associativa, como tabela
    if ($usuario && is_array($usuario)) {
        // A consulta retornou resultados e $usuario é um array
        $senha_banco = $usuario['senha'];
        if (password_verify($senha, $senha_banco)) {
            //Criar um token
            $token = sha1(uniqid() . date('d-m-Y-H-i-s'));
            //Atualizar o token deste usuario no banco
            $sql = $pdo->prepare("UPDATE usuario SET token=? WHERE usuario=?");
            $sql->execute(array($token, $name));
            //Armazenar este token na sessão
            $_SESSION['TOKEN'] = $token;
            $_SESSION['mensagem'] = "Login com sucesso!";
            header('location: index.php?page=game');
        } else {
            $_SESSION['mensagemerro'] = "Dados incorretos, tente novamente!";
        }
    } else {
        $_SESSION['mensagemerro'] = "Dados incorretos, tente novamente!";
    }
}

function limpaPost($dados)
{
    $dados = trim($dados);
    $dados = stripslashes($dados);
    $dados = htmlspecialchars($dados);
    return $dados;
}

function auth($tokenSessao)
{
    global $pdo;
    $sql = $pdo->prepare("SELECT * FROM usuario WHERE token=? LIMIT 1");
    $sql->execute(array($tokenSessao));
    $usuario = $sql->fetch(PDO::FETCH_ASSOC);
    //Se não encontrar o usuario
    if (!$usuario) {
        return false;
    } else {
        return $usuario;
    }
}

function sessionVerif()
{
    global $usuario;
    $usuario = auth($_SESSION['TOKEN']);
    if (!$usuario) {
        header('location: index.php?page=login');
    }
}

// INICIO --- Notificações //
function notyfOK() //NOTIFICAÇÃO OK
{
    if (isset($_SESSION['mensagem'])) {
        $mensagem = $_SESSION['mensagem'];
        ?>
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/notyf@3/notyf.min.css">
        <script src="https://cdn.jsdelivr.net/npm/notyf@3/notyf.min.js"></script>
        <script type="text/javascript">
            var mensagem = <?php echo json_encode($mensagem); ?>;
            var notyf = new Notyf();
            notyf.success(mensagem);
            <?php unset($_SESSION['mensagem']); ?>
        </script>
    <?php }
}
register_shutdown_function('notyfOK'); // Realizar a verificação após o carregamento de tudo

function notyfERRO() //NOTIFICAÇÃO ERRO
{
    if (isset($_SESSION['mensagemerro'])) {
        $mensagemerro = $_SESSION['mensagemerro'];
        ?>
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/notyf@3/notyf.min.css">
        <script src="https://cdn.jsdelivr.net/npm/notyf@3/notyf.min.js"></script>
        <script type="text/javascript">
            var mensagemerro = <?php echo json_encode($mensagemerro); ?>;
            var notyf = new Notyf();
            notyf.error(mensagemerro);
            <?php unset($_SESSION['mensagemerro']); ?>
        </script>
    <?php }
}
register_shutdown_function('notyfERRO'); // Realizar a verificação após o carregamento de tudo
// FIM --- Notificações //