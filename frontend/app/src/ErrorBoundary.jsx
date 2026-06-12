import React from 'react';

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  static getDerivedStateFromError(error) {
    // Mettre à jour l'état pour que le prochain rendu affiche l'UI de fallback.
    return { hasError: true };
  }

  componentDidCatch(error, errorInfo) {
    // Vous pouvez aussi enregistrer l'erreur dans un service de rapport d'erreurs
    console.error("Erreur non capturée par l'ErrorBoundary:", error, errorInfo);
    this.setState({ error, errorInfo });
  }

  render() {
    if (this.state.hasError) {
      // Vous pouvez rendre n'importe quelle UI de fallback.
      return (
        <div style={{ padding: '20px', textAlign: 'center', fontFamily: 'sans-serif', color: '#ef4444', backgroundColor: '#ffebeb', border: '1px solid #ef4444', borderRadius: '8px', margin: '20px' }}>
          <h1>Oups ! Quelque chose s'est mal passé.</h1>
          <p>Nous sommes désolés pour le désagrément. Veuillez réessayer plus tard.</p>
          {this.state.error && (
            <details style={{ whiteSpace: 'pre-wrap', textAlign: 'left', marginTop: '15px', borderTop: '1px solid #ef4444', paddingTop: '10px' }}>
              <summary>Détails de l'erreur</summary>
              {this.state.error.toString()}
              <br />
              {this.state.errorInfo.componentStack}
            </details>
          )}
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;