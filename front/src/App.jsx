import { useState } from 'react'
import reactLogo from './assets/react.svg'
import viteLogo from '/vite.svg'
import './App.css'

function fetchAllParts(){
    console.log('click fue hecho')
    fetch("http://127.0.0.1:5000/part/parts")
    .then(response => response.json())
    .then(data => {
        console.log(data);
    });
}



function App() {
  const [count, setCount] = useState(0)

  return (
    <>

      <h1>Vite + React</h1>
      <div className="card">
        <button onClick={fetchAllParts}>
          count is {count}
        </button>
      </div>
    </>
  )
}

export default App
