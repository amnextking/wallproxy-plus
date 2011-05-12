<?php

# __author__ = 'base64.decodestring("d3d3LmVodXN0QGdtYWlsLmNvbQ==")'
# __version__ = '0.2.2'

function _unquote_data($s) {
	$unquote_map = array("\x102"=>'&', "\x101"=>'=', "\x100"=>"\x10");
	return str_replace(array_keys($unquote_map), array_values($unquote_map), $s);
}

function decode_data($qs, $keep_blank_values=False) {
	$pairs = explode('&', $qs);
	$dic = array();
	foreach ($pairs as $name_value) {
		if (!$name_value && !$keep_blank_values)
			continue;
		$nv = explode('=', $name_value, 2);
		if (count($nv) != 2) {
			if ($keep_blank_values)
				$nv[] = '';
			else continue;
		}
		if (strlen($nv[1]) || $keep_blank_values)
			$dic[_unquote_data($nv[0])] = _unquote_data($nv[1]);
	}
	return $dic;
}

function _quote_data($s) {
	$quote_map = array("\x10"=>"\x100", '='=>"\x101", '&'=>"\x102");
	return str_replace(array_keys($quote_map), array_values($quote_map), $s);
}

function encode_data($dic) {
	$res = array();
	foreach ($dic as $k=>$v)
		$res[] = _quote_data($k).'='._quote_data($v);
	return implode('&', $res);
}

function xor_data($data, $key) {
	$key_len = strlen($key);
	if ($key_len == 0)
		return $data;
	$data_len = strlen($data);
	for ($i=0; $i<$data_len; $i++) {
		$data[$i] = chr(ord($data[$i]) ^ ord($key[$i % $key_len]));
	}
	return $data;
}

class MainHandler {
	protected $siteKey = '\xcf\x83\xe15~\xef\xb8\xbd\xf1T(P\xd6m\x80\x07\xd6 \xe4\x05\x0bW\x15\xdc\x83\xf4\xa9!\xd3l\xe9\xce';
	protected $fetchMax = 2;
	protected $contentMax = 200000;
	protected $code = 0;
	protected $headers = array();

	function __construct() {
#		$this->logFile = dirname(__FILE__).'/fetch.log';
	}

	protected function sendResponse($code, $headers, $content='') {
		header('Content-Type: application/octet-stream');
		$headers = encode_data($headers);
		$raw_data = pack('N3', $code, strlen($headers), strlen($content)).$headers.$content;
		if ($code == 206) {
			$data = '0'.$raw_data;
		} else {
			$data = gzcompress($raw_data, 9);
			$data = strlen($raw_data) > strlen($data) ? '1'.$data : '0'.$raw_data;
		}
		echo xor_data($data, $this->siteKey);
		header('Content-Length: ' . ob_get_length());
	}

	protected function sendNotify($status_code, $content, $fullContent=False) {
		if (!$fullContent && $status_code!=555)
			$content = '<h2>Fetch Server Info</h2><hr noshade="noshade"><p>Code: '.
						$status_code.'</p><p>Message: '.$content.'</p>';
		$headers = array('server'=>'WallProxy/0.2', 'content-type'=>'text/html',
						'content-length'=>strlen($content));
		$this->sendResponse($status_code, $headers, $content);
	}

	function readHeader($ch, $header) {
		$kv = array_map('trim', explode(':', $header, 2));
		if (count($kv) == 2) {
			$kv[0] = strtolower($kv[0]);
			if ($kv[0]=='content-length' && $kv[1]>$this->contentMax) {
				$this->code = -1;
				return -1;
			}
			$key = ucwords($kv[0]);
			if (!array_key_exists($key, $this->headers))
				$this->headers[$key] = $kv[1];
			else
				$this->headers[$key] .= "\r\n{$key}: {$kv[1]}";
		}
		return strlen($header);
	}

	protected function post() {
		$request = xor_data(file_get_contents('php://input'), $this->siteKey);
		$request = @gzuncompress($request);
		if ($request === False) {
            echo 'Hello World!';
            return;
        }
		$request = decode_data($request);

		$url_parts = parse_url($request['url']);
		if (!in_array(strtolower($url_parts['scheme']), array('http', 'https')))
			return $this->sendNotify(555, 'Unsupported Scheme');
		if (strtolower($url_parts['host']) == 'wallproxy')
			return $this->sendNotify(200, '<h2>Welcome!</h2><hr noshade="noshade"><p>WallProxy is running.</p>', True);
		if (!empty($this->logFile) && ($fh = @fopen($this->logFile, 'a'))) {
			$curl_opt[CURLOPT_STDERR] = $fh;
			$curl_opt[CURLOPT_VERBOSE] = True;
		}
		$curl_opt[CURLOPT_TIMEOUT] = 30;
		$curl_opt[CURLOPT_SSL_VERIFYPEER] = False;
		$curl_opt[CURLOPT_SSL_VERIFYHOST] = False;
		$curl_opt[CURLOPT_HEADERFUNCTION] = array(&$this, 'readHeader');
		$curl_opt[CURLOPT_RETURNTRANSFER] = True;
		switch ($request['method']) {
		case 'HEAD':
			$curl_opt[CURLOPT_NOBODY] = True;
			break;
		case 'GET':
			break;
		case 'PUT':
		case 'POST':
		case 'DELETE':
			$curl_opt[CURLOPT_CUSTOMREQUEST] = $request['method'];
			$curl_opt[CURLOPT_POSTFIELDS] = $request['payload'];
			break;
		default:
			return $this->sendNotify(555, 'Invalid Method');
		}

		foreach (explode("\n", $request['headers']) as $line) {
			if (strpos($line, ':') === False)
				continue;
			list($key, $value) = explode(':', $line, 2);
			$key = strtolower(trim($key));
			$curl_opt[CURLOPT_HTTPHEADER][$key] = trim($line);
		}
		$curl_opt[CURLOPT_HTTPHEADER]['connection'] = 'Connection: close';
		#error_log(print_r($curl_opt[CURLOPT_HTTPHEADER], True));

		$ch = curl_init($request['url']);
		curl_setopt_array($ch, $curl_opt);
		for ($i=0; $i<$this->fetchMax; $i++) {
			$content = curl_exec($ch);
			if ($this->code == -1) {
				if ($request['method'] != 'GET') {
					curl_close($ch);
					return $this->sendNotify(555, 'Urlfetch error: Response is larger than '.$this->contentMax.' bytes');
				}
				if ($request['range']) $curl_opt[CURLOPT_HTTPHEADER]['range'] = $request['range'];
				curl_setopt($ch, CURLOPT_HTTPHEADER, $curl_opt[CURLOPT_HTTPHEADER]);
				$this->code = 0;
				continue;
			}
			$errno = curl_errno($ch);
			$error = curl_error($ch);
			if ($errno == 0) {
				$this->code = curl_getinfo($ch, CURLINFO_HTTP_CODE);
				curl_close($ch);
				#error_log("Status: {$this->code}\n".print_r($this->headers, True));
				return $this->sendResponse($this->code, $this->headers, $content);
			}
			if ($errno <= 7)
				break;
			error_log("Urlfetch error: [$errno]$error");
		}
		curl_close($ch);
		return $this->sendNotify(555, "Urlfetch error: [$errno]$error");
	}

	protected function get() {
		header('Location: http://twitter.com/hexieshe');
	}

	function run() {
		ob_start();
		$method = strtoupper($_SERVER['REQUEST_METHOD']);
		$method=='POST' ? $this->post() : $this->get();
	}
}

$handler = new MainHandler();
$handler->run();