# Alpha Names — verificador experimental Discord

O projeto tem geração de **3L / Semi-3L / 4L / Semi-4L**, quantidade personalizada, busca, exportação e agora consultas reais **experimentais** via servidor Python. As consultas usam um endpoint de disponibilidade que não consta da API pública documentada para bots. **Podem falhar** por limitação, bloqueio de origem, mudança no endpoint ou reserva de nomes. Somente resposta HTTP 200 com `taken: true` ou `taken: false` é exibida como **ocupado** ou **disponível**. Não é garantia de conseguir registrar o nome.

## Publicar tudo pelo iPhone com GitHub e Render (recomendado)

1. Extraia o ZIP no app Arquivos e envie os **5 arquivos da raiz** (`index.html`, `app.py`, `requirements.txt`, `render.yaml`, `README.md`) para um repositório GitHub pelo Safari. Se o repositório atual contém `index.html`, substitua-o, e adicione os outros quatro arquivos.
2. No [Render](https://dashboard.render.com/), crie **New → Web Service** e selecione esse repositório.
3. Configure **Language: Python**, **Build Command**: `pip install -r requirements.txt`, **Start Command**: `gunicorn app:app --workers 1 --threads 2 --timeout 60`, plano Free.
4. Não há necessidade de adicionar tokens ou senhas de Discord em Environment Variables. Faça o deploy.
5. Abra o link `.onrender.com`. A caixa **Servidor da consulta** pode ficar vazia nesse caso, porque o site e o verificador estão na mesma origem.

## Se quiser manter o site atual no GitHub Pages

- Substitua o `index.html` do GitHub Pages pelo deste ZIP.
- Publique **também** o backend no Render com os demais arquivos.
- No site do GitHub Pages, digite a URL HTTPS do seu serviço Render na caixa **Servidor da consulta (Render)**, toque **Testar servidor**, e só então **Verificar próximos 20** ou **Consultar** em um nome.

## Limites e interpretação

- Consulta sequencial: no máximo 20 por lote, com espera de 4,5 segundos entre requisições; o servidor limita a aproximadamente 1 consulta a cada 4 segundos. Se o servidor exigir intervalo, ele interrompe o lote; respeite os bloqueios.
- Arquivos e nomes gerados ficam no armazenamento local do navegador, mas o backend recebe cada nome enviado para consulta. Nenhuma senha ou token de conta Discord é solicitada.
- Respostas HTTP 401/403, 429, 5xx, CORS, erros de rede, HTML inesperado ou JSON sem booleano `taken` nunca são interpretadas como livres.
- Caso queira restringir quais sites podem chamar a API, defina `ALLOWED_ORIGIN` em Environment Variables com a origem exata do seu GitHub Pages (`https://seu-usuario.github.io`); o padrão `*` permite consulta pública, com limitação global de frequência.
- O endpoint não é oficial para terceiros e pode parar de funcionar. Verificação definitiva: Configurações do Discord → Conta → Nome de usuário.

Regras oficiais: https://support.discord.com/hc/pt-br/articles/12620128861463-Novos-nomes-de-usu%C3%A1rio-e-nomes-de-exibi%C3%A7%C3%A3o
