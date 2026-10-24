Guarda a feature de cadastro, login e regras relacionadas aos usuários.

O acesso Proprietário do cabeçalho abre `/configuracoes`, com nome do comércio e foto de perfil. O nome personaliza todas as páginas e o login; a foto é individual e pode ser substituída sem alterar os dados de outros usuários. O envio aceita JPG, PNG ou WebP de até 2 MB, com validação no servidor e prévia no navegador. Os bytes são persistidos no PostgreSQL e servidos por `/configuracoes/foto-perfil` somente ao próprio usuário, sem dependência de diretórios públicos de mídia.
