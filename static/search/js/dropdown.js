document.getElementById("sort-by").onchange = function() {
  let search_url = new URL(window.location.href)
  let current_params = new URLSearchParams(search_url.search)

  if (this.value) {
    current_params.set('order', this.value)
  } else {
    current_params.delete('order')
  }

  search_url.search = current_params.toString()
  window.location.href = search_url.toString()
}
