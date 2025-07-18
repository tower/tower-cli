echo "Checking for openssl-sys in dependency tree..."
if cargo tree -i openssl-sys >/dev/null 2>&1; then
	echo "openssl-sys is present in the dependency tree. Please evict it."
	exit 1
fi

echo "Checking for native-tls in dependency tree..."
if cargo tree -i native-tls >/dev/null 2>&1; then
	echo "native-tls is present in the dependency tree. Please evict it."
	exit 1
fi

echo "✅ No naughty dependencies found"
