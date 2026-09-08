export default function NotebookSpread({ leftPage, rightPage }) {
  return (
    <div className="notebook-spread">
      <div className="notebook-page notebook-page-left">{leftPage}</div>
      <div className="notebook-spine" />
      <div className="notebook-page notebook-page-right">{rightPage}</div>
    </div>
  )
}