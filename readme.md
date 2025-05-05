# SSTC

 Controle de Samsung via terminal, com interface interativa oldschool.  
Inspirado no projeto `homebridge-samsung-tizen`

Escrito numa noite de insônia com café e raiva do controle remoto.

---

## Requisitos

- Python 3.6+
- Dependências Python:
  ```bash
  pip install websocket-client requests
  ```

---

##  Como usar

```bash
python3 sstc.py
```

Digite o IP da sua TV.

---

##  Controles Interativos

Após conectar, você entra no **modo interativo**. Use as teclas abaixo:

| Tecla       | Função                              |
|-------------|--------------------------------------|
| w / a / s / d | Navegação ↑ ← ↓ →                  |
| e           | Enter / OK                           |
| espaço      | Play / Pause                         |
| + / -       | Aumentar / Reduzir volume            |
| p           | Power Toggle (liga/desliga)          |
| 0–9         | Teclas numéricas                     |
| l           | Listar todos os comandos da TV       |
| x           | Abrir menu de aplicativos            |
| c           | Enviar comando customizado (JSON)    |
| h / ?       | Mostrar o menu de ajuda              |
| q           | Sair do modo interativo              |

---

##  Recursos

- Conexão com WebSocket (`wss`)
- Reconhecimento e armazenamento de token local
- Controle remoto com suporte a:
  - Teclas virtuais
  - Volume / canais
  - Apps instalados (Netflix, YouTube, Disney+, etc.)
  - Comandos personalizados

---

##  Créditos

Projeto inspirado na engenharia reversa feita por:
 https://tavicu.github.io/homebridge-samsung-tizen/

Thanks ao Tavicu & co pelo trabalho impecável com TVs Samsung.

---

##  Autor

**AgniK4i**  
GitHub: [github.com/agnik4i](https://github.com/agnik4i)

---

## Aviso Legal

Este projeto não é afiliado à Samsung.  
Use por sua conta e risco. Não espere suporte.  
E lembre-se: escrevi baseado na MINHA TV — se não funcionar na sua, de seus pulos 👀
