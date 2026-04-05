//Datatable
$(document).ready(function () {
    //Com responsividade e tradução
    $('#tabela-ranking').DataTable({
        responsive: true,
        "language": {
            "emptyTable": "Nenhum registro encontrado",
            "info": "Mostrando de _START_ até _END_ de _TOTAL_ registros",
            "infoEmpty": "Mostrando 0 até 0 de 0 registros",
            "infoFiltered": "(Filtrados de _MAX_ registros)",
            "infoThousands": ".",
            "loadingRecords": "Carregando...",
            "processing": "Processando...",
            "zeroRecords": "Nenhum registro encontrado",
            "search": "Pesquisar",
            "lengthMenu": "Exibir _MENU_ resultados por página",
            "paginate": {
                "next": ">",
                "previous": "<",
                "first": "Primeiro",
                "last": "Último"
            }
        },
        "order": [
            [1, 'desc']
        ]
    });
});
//FIM