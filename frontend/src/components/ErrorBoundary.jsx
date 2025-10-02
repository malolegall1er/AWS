import React from 'react';

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null, info: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, info) {
    // You could send this to a logging service
    // eslint-disable-next-line no-console
    console.error('ErrorBoundary caught an error', error, info);
    this.setState({ info });
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{
          padding: '16px',
          margin: '16px',
          borderRadius: '8px',
          background: '#ffe8e8',
          color: '#8b0000',
          border: '1px solid #ffb3b3',
          fontFamily: 'system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif'
        }}>
          <h2>Une erreur est survenue dans l'interface</h2>
          <p>Ouvre la console du navigateur (F12) pour plus de détails.</p>
          {this.state.error && (
            <pre style={{ whiteSpace: 'pre-wrap' }}>{String(this.state.error)}</pre>
          )}
        </div>
      );
    }
    return this.props.children;
  }
}

export default ErrorBoundary;
