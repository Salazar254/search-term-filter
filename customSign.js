// Dummy signing script - electron-builder requires a sign function but we'll skip it
module.exports = async function(configuration) {
  console.log('Signing disabled for development build');
  return null;
};
