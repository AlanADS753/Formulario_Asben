const API_URL = "http://localhost:5000";

        const form        = document.getElementById('cadastroForm');
        const telaSucesso = document.getElementById('tela-sucesso');
        const inputFoto   = document.getElementById('foto');
        const previewWrap = document.getElementById('preview-wrap');
        const previewImg  = document.getElementById('preview-img');
        const nomeArquivo = document.getElementById('nome-arquivo');
        const btnRemover  = document.getElementById('remover-foto');
        const toast       = document.getElementById('toast');
        const inpDia      = document.getElementById('inp-dia');
        const inpMes      = document.getElementById('inp-mes');
        const inpAno      = document.getElementById('inp-ano');

        // Segmented date
        function soNumeros(e) { e.target.value = e.target.value.replace(/\D/g, ''); }
        inpDia.addEventListener('input', e => { soNumeros(e); if (e.target.value.length === 2) inpMes.focus(); });
        inpMes.addEventListener('input', e => { soNumeros(e); if (e.target.value.length === 2) inpAno.focus(); });
        inpAno.addEventListener('input', soNumeros);

        function getDataISO() {
            return `${inpAno.value}-${inpMes.value.padStart(2,'0')}-${inpDia.value.padStart(2,'0')}`;
        }
        function dataValida() {
            const d = parseInt(inpDia.value), m = parseInt(inpMes.value), a = parseInt(inpAno.value);
            return d >= 1 && d <= 31 && m >= 1 && m <= 12 && a >= 1900 && a <= 2100;
        }

        // Preview foto
        inputFoto.addEventListener('change', () => {
            const file = inputFoto.files[0];
            if (!file) return;
            nomeArquivo.textContent = file.name;
            previewImg.src = URL.createObjectURL(file);
            previewWrap.style.display = 'block';
        });
        btnRemover.addEventListener('click', () => {
            inputFoto.value = '';
            previewWrap.style.display = 'none';
            nomeArquivo.textContent = 'Clique para selecionar uma imagem';
        });

        function cpfValido(cpf) { return /^\d{11}$/.test(cpf); }

        let toastTimer;
        function mostrarToast(msg, tipo = 'ok') {
            clearTimeout(toastTimer);
            toast.textContent = msg;
            toast.className   = `show ${tipo}`;
            toastTimer = setTimeout(() => { toast.className = ''; }, 4000);
        }

        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            const btn  = document.getElementById('btn-enviar');
            const nome = document.getElementById('nome').value.trim();
            const cpf  = document.getElementById('cpf').value.trim();
            const foto = inputFoto.files[0];

            if (!cpfValido(cpf)) { mostrarToast('CPF inválido — use apenas 11 números.', 'erro'); return; }
            if (!dataValida())   { mostrarToast('Data de nascimento inválida.', 'erro'); return; }

            btn.disabled  = true;
            btn.innerHTML = '<span class="spinner"></span>Enviando...';

            try {
                const payload = new FormData();
                payload.append('nome',      nome);
                payload.append('cpf',       cpf);
                payload.append('data_nasc', getDataISO());
                if (foto) payload.append('foto', foto);

                const resposta = await fetch(`${API_URL}/cadastrar`, { method: 'POST', body: payload });
                const json = await resposta.json();

                if (json.sucesso) {
                    form.reset();
                    inpDia.value = ''; inpMes.value = ''; inpAno.value = '';
                    previewWrap.style.display = 'none';
                    nomeArquivo.textContent   = 'Clique para selecionar uma imagem';
                    form.classList.add('hidden');
                    telaSucesso.classList.remove('hidden');
                } else {
                    mostrarToast(json.mensagem || 'Erro ao cadastrar.', 'erro');
                }
            } catch (err) {
                mostrarToast('Não foi possível conectar ao servidor.', 'erro');
                console.error(err);
            } finally {
                btn.disabled  = false;
                btn.innerHTML = 'CADASTRAR';
            }
        });

        function voltarAoFormulario() {
            telaSucesso.classList.add('hidden');
            form.classList.remove('hidden');
        }