# 🎨 Assets do Projeto

Esta pasta contém todos os recursos visuais e arquivos de mídia do projeto Indicadores-COMG.

## 📁 Conteúdo

### 🖼️ Imagens e Logos
- **[Marca_Drumond Soluções Hospitalares-01.png](./Marca_Drumond%20Soluções%20Hospitalares-01.png)** - Logo oficial da Drumond Soluções Hospitalares

## 📋 Diretrizes de Uso

### Formatos Suportados
- **Imagens**: PNG, JPG, SVG
- **Ícones**: SVG (preferencialmente)
- **Logos**: PNG com fundo transparente

### Organização
```
assets/
├── logos/          # Logos e marcas
├── icons/          # Ícones da interface
├── images/         # Imagens gerais
└── screenshots/    # Capturas de tela
```

### Nomenclatura
- Use nomes descritivos em português
- Separe palavras com hífen ou underscore
- Inclua dimensões quando relevante (ex: `logo-200x100.png`)
- Use versioning para diferentes versões (ex: `logo-v1.png`, `logo-v2.png`)

## 🎯 Uso na Aplicação

### Streamlit
```python
import streamlit as st

# Carregar logo
st.image("assets/logos/Marca_Drumond Soluções Hospitalares-01.png", width=200)
```

### HTML/CSS
```html
<img src="assets/logos/logo.png" alt="Logo Drumond" />
```

## 📝 Manutenção

- Mantenha backups dos arquivos originais
- Otimize imagens para web (compressão adequada)
- Use formatos vetoriais quando possível
- Documente licenças e direitos autorais

---

*Última atualização: 25 de julho de 2025*
