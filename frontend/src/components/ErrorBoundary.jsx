import { Component } from 'react'

/** Shows a readable message instead of a blank page if a component crashes. */
export default class ErrorBoundary extends Component {
  constructor(props) {
    super(props)
    this.state = { error: null }
  }

  static getDerivedStateFromError(error) {
    return { error }
  }

  reset = () => {
    try {
      sessionStorage.clear()
    } catch {
      /* ignore */
    }
    window.location.assign('/')
  }

  render() {
    if (!this.state.error) return this.props.children
    return (
      <div className="card mx-auto max-w-xl space-y-3 p-8 text-center">
        <h1 className="text-xl font-semibold text-slate-900">This page could not be displayed</h1>
        <p className="text-sm text-slate-600">{String(this.state.error.message || this.state.error)}</p>
        <button type="button" className="btn-primary" onClick={this.reset}>
          Start a new session
        </button>
      </div>
    )
  }
}
