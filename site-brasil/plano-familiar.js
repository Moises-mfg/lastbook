// Dados apenas na página: sem envio, armazenamento ou bibliotecas externas.
(() => {
  const fields = [...document.querySelectorAll('input, textarea')];
  function updatePrintValues() {
    for (const field of fields) field.nextElementSibling.textContent = field.value;
  }
  for (const field of fields) field.addEventListener('input', updatePrintValues);
  window.addEventListener('beforeprint', updatePrintValues);
  updatePrintValues();
  document.documentElement.classList.add('print-ready');
  const printButton = document.getElementById('imprimir-plano');
  printButton.hidden = false;
  printButton.addEventListener('click', () => {
    updatePrintValues();
    window.print();
  });
})();
