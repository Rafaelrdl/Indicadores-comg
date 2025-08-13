import streamlit as st
import streamlit.components.v1


def inject_global_css() -> None:
    st.markdown(
        """
        <style>
          section[data-testid='stSidebar'] { 
            order: 0; 
            border-right: 1px solid #eee; 
            border-left: none;
          }
          div.block-container { 
            padding-left: 2rem; 
            padding-right: 1rem;
          }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Adicionar JavaScript mais robusto
    st.components.v1.html(
        """
        <script>
        function updateMainLink() {
            setTimeout(function() {
                const mainLink = document.querySelector('a[data-testid="stSidebarNavLink"][href="/"]');
                if (mainLink) {
                    const span = mainLink.querySelector('span');
                    if (span && span.textContent.trim() === 'main') {
                        span.textContent = 'Tela Principal';
                    }
                }
            }, 100);
        }
        
        // Execute multiple times to ensure it works
        updateMainLink();
        document.addEventListener('DOMContentLoaded', updateMainLink);
        
        // Use MutationObserver to watch for changes
        if (typeof MutationObserver !== 'undefined') {
            const observer = new MutationObserver(updateMainLink);
            observer.observe(document.body, { childList: true, subtree: true });
        }
        </script>
        """,
        height=0,
    )
