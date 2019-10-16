#!/usr/bin/perl
use CGI::Carp qw(fatalsToBrowser);
use Data::Dumper;

use LWP::Simple;
use XML::Simple;
use URI::Escape;
use List::Util qw[min max];


#use SOAP::Lite;
use DB_File;
require 'cgi-lib.pl';

&ReadParse(*input);
$user = $input{user};
$type = $input{type};
$day = $input{day};
$quant = $input{quant};
$price = $input{price};

$valid = 1;

tie %holdingsStock, 'DB_File', "holdingsStock", O_CREAT|O_RDWR, 0666, $DB_HASH or die "cannot open hash\n";
tie %holdingsCash, 'DB_File', "holdingsCash", O_CREAT|O_RDWR, 0666, $DB_HASH or die "cannot open hash\n";

tie %buyorderday, 'DB_File', "buyorderday", O_CREAT|O_RDWR, 0666, $DB_HASH or die "cannot open hash\n";
tie %buyorderquant, 'DB_File', "buyorderquant", O_CREAT|O_RDWR, 0666, $DB_HASH or die "cannot open hash\n";
tie %buyorderprice, 'DB_File', "buyorderprice", O_CREAT|O_RDWR, 0666, $DB_HASH or die "cannot open hash\n";
tie %buyorderuser, 'DB_File', "buyorderuser", O_CREAT|O_RDWR, 0666, $DB_HASH or die "cannot open hash\n";

tie %sellorderday, 'DB_File', "sellorderday", O_CREAT|O_RDWR, 0666, $DB_HASH or die "cannot open hash\n";
tie %sellorderquant, 'DB_File', "sellorderquant", O_CREAT|O_RDWR, 0666, $DB_HASH or die "cannot open hash\n";
tie %sellorderprice, 'DB_File', "sellorderprice", O_CREAT|O_RDWR, 0666, $DB_HASH or die "cannot open hash\n";
tie %sellorderuser, 'DB_File', "sellorderuser", O_CREAT|O_RDWR, 0666, $DB_HASH or die "cannot open hash\n";

tie %marketprice, 'DB_File', "marketprice", O_CREAT|O_RDWR, 0666, $DB_HASH or die "cannot open hash\n";

print "Content-type: text/html; charset=UTF-8\n\n";
# some html code...
print '<html><head><title>Information Market</title>
<STYLE TYPE="text/css">
    A:link, A:visited { font color="#0000FF" }
		    td {font-family: Arial; }
					</STYLE>

						 </head><body>';
if (!defined($holdingsCash{$user})) {
	print "invalid user $user<br>\n";
	$valid = 0;
}

if (($type ne "sell")&&($type ne "buy")) {
	print "invalid transaction type: $type\n";
	$valid = 0;
}

if (($quant < 1)) {
	print "invalid quantity $quant\n";
	$valid = 0;
}

if ($price <= 0) {
	print "invalid price $price\n";
	$valid = 0;
}


if ($type eq "sell") {
$sellerday = "$user:$day";
if ($holdingsStock{$sellerday} < $quant) {
	print "you don't have that much stock to sell: $quant vs. $holdingsStock{$sellerday}\n";
	$valid = 0;
}
}

if ($valid) {
	open(OUT,">> log.txt");
if ($type eq "sell") {
	print "user $user submitted order to sell $quant of April $day for $price<br>\n";
	print OUT "user $user submitted order to sell $quant of April $day for $price<br>\n";
	$orderid =  localtime(time);
	$sellorderday{$orderid} = $day;
	$sellorderprice{$orderid} = $price;
	$sellorderquant{$orderid} = $quant;
	$sellorderuser{$orderid} = $user;
	$so = $orderid;

	$alldone = 0;
	for $bo (sort {$buyorderprice{$b}<=>$buyorderprice{$a};} keys %buyorderprice) {
		last if ($alldone);
		print "buy $buyorderprice{$bo} vs. sell $sellorderprice{$so}, $buyorderday{$bo} vs. $sellorderday{$so}\n";
		if ($buyorderprice{$bo} < $sellorderprice{$so}) {$alldone = 1;}
		if (($buyorderprice{$bo} >= $sellorderprice{$so})&&($buyorderday{$bo} == $sellorderday{$so})) {
#			print "FOUND MATCH!!!!\n<br>\n";
			$theprice = $sellorderprice{$so};
			if ($sellorderquant{$so} >= $buyorderquant{$bo}) {
				$tradequant = $buyorderquant{$bo};
			} else {
				$tradequant = $sellorderquant{$so};
			}
			$buyer = $buyorderuser{$bo};
			$themoney = $tradequant*$theprice;
			$buyerday = "$buyer:$buyorderday{$bo}";
			$sellerday = "$user:$sellorderday{$so}";
			if (($holdingsCash{$buyer} >= $themoney)&&($holdingsStock{$sellerday}>=$tradequant)) {
				$holdingsCash{$buyer} -= $themoney;
				$holdingsCash{$user} += $themoney;
				$holdingsStock{$buyerday} += $tradequant;
				$holdingsStock{$sellerday} -= $tradequant;
				$buyorderquant{$bo} = $buyorderquant{$bo} - $tradequant;
				$sellorderquant{$so} = $sellorderquant{$so} - $tradequant;
				if ($sellorderquant{$so} == 0) {
					delete $sellorderquant{$so};
					delete $sellorderuser{$so};
					delete $sellorderprice{$so};
					delete $sellorderday{$so};
					$alldone = 1;
				} 
				if ($buyorderquant{$bo} == 0) {
					delete $buyorderquant{$bo};
					delete $buyorderuser{$bo};
					delete $buyorderprice{$bo};
					delete $buyorderday{$bo};
				}
				print "$tradequant stock(s) of April $buyorderday{$bo} from $user to $buyer for $theprice<br>\n"; 
				print OUT "$tradequant stock(s) of April $buyorderday{$bo} from $user to $buyer for $theprice<br>\n"; 
				$marketprice{$buyorderday{$bo}} = $theprice;
				print OUT "marketprice $buyorderday{$bo}: $theprice\n";
			}
		}
	}
} elsif ($type eq "buy") {
	print "user $user submitted order to buy $quant of April $day for $price<br>\n";
	print OUT "user $user submitted order to buy $quant of April $day for $price<br>\n";
	$orderid =  localtime(time);
	$buyorderday{$orderid} = $day;
	$buyorderprice{$orderid} = $price;
	$buyorderquant{$orderid} = $quant;
	$buyorderuser{$orderid} = $user;
	$bo = $orderid;
	$buyer = $user;

	$alldone = 0;
	for $so (sort {$sellorderprice{$a}<=>$sellorderprice{$b};} keys %sellorderprice) {
		if ($buyorderprice{$bo} < $sellorderprice{$so}) {$alldone = 1;}
		last if ($alldone);
		print "$buyorderprice{$bo} vs. $sellorderprice{$so}, $buyorderday{$bo} vs. $sellorderday{$so}\n";
		if (($buyorderprice{$bo} >= $sellorderprice{$so})&&($buyorderday{$bo} == $sellorderday{$so})) {
#			print "FOUND MATCH for buy order!!!!\n<br>\n";
			$theprice = $sellorderprice{$so};
			if ($sellorderquant{$so} >= $buyorderquant{$bo}) {
				$tradequant = $buyorderquant{$bo};
			} else {
				$tradequant = $sellorderquant{$so};
			}
			$seller = $sellorderuser{$so};
			$themoney = $tradequant*$theprice;
			$buyerday = "$buyer:$buyorderday{$bo}";
			$sellerday = "$seller:$buyorderday{$bo}";
			if (($holdingsCash{$buyer} >= $themoney)&&($holdingsStock{$sellerday}>=$tradequant)) {
				$holdingsCash{$buyer} -= $themoney;
				$holdingsCash{$seller} += $themoney;
				$holdingsStock{$buyerday} += $tradequant;
				$holdingsStock{$sellerday} -= $tradequant;
				$buyorderquant{$bo} = $buyorderquant{$bo} - $tradequant;
				$sellorderquant{$so} = $sellorderquant{$so} - $tradequant;
				if ($sellorderquant{$so} == 0) {
					delete $sellorderquant{$so};
					delete $sellorderuser{$so};
					delete $sellorderprice{$so};
					delete $sellorderday{$so};
				} 
				if ($buyorderquant{$bo} == 0) {
					delete $buyorderquant{$bo};
					delete $buyorderuser{$bo};
					delete $buyorderprice{$bo};
					delete $buyorderday{$bo};
					$alldone = 1;
				}

				print "$tradequant stock(s) of April $buyorderday{$bo} from $seller to $buyer for $theprice<br>\n"; 
				print OUT "$tradequant stock(s) of April $buyorderday{$bo} from $seller to $buyer for $theprice<br>\n"; 
				$marketprice{$buyorderday{$bo}} = $theprice;
				print OUT "marketprice $buyorderday{$bo}: $theprice\n";
			}
		}
	}
}
close(OUT);
}

print "<table><tr><td>\n";
print '<form action="infomarket.cgi" method="POST" target="_blank">
username: <input type="text" name="user">  <br>
quantity: <input type="text" name="quant">  <br>
price: <input type="text" name="price">  <br>
<select name="day">
<option value="20" selected>April 20<option>
<option value="21">April 21<option>
<option value="22">April 22<option>
<option value="23">April 23<option>
<option value="24">April 24<option>
<option value="25">April 25<option>
</select>

<input type="radio" name="type" value="buy"> BUY 
<input type="radio" name="type" value="sell"> SELL
<input type="submit" value="SUBMIT">
</form><br>';

print "</td><td><table border = 1><tr><th>Day</th><th>Market Price</th></tr>\n";
for ($i = 20; $i < 25; $i++) {
	print "<tr><td>April $i</td><td> $marketprice{$i}</td></tr>\n";
}
print "<tr><td>April 25</td><td>".$marketprice{"25"}."</td></tr></table>\n";
print "</td></tr></table>\n";

print "<table border = 1><tr><td>\n";
  print "<table><tr>
	  <th>user</th><th>cash</th><th>April 20</th><th>April 21</th><th>April 22</th><th>April 23</th><th>April 24</th><th>April 25th</th></tr>\n";
		for $key (keys %holdingsCash) {
			  print "<tr><td>$key</td><td>$holdingsCash{$key}</td><td>".$holdingsStock{"$key:20"}."</td><td>".$holdingsStock{"$key:21"}."</td><td>".$holdingsStock{"$key:22"}."</td><td>".
				  $holdingsStock{"$key:23"}."</td><td>".$holdingsStock{"$key:24"}."</td><td>".$holdingsStock{"$key:25"}."</td></tr>\n";
		}

  print "</table>\n";
	print "</td><td valign=\"top\">\n";

	print "<b>Buy Orders</b><br>\n";
for $key (sort {$b <=> $a;} keys %buyorderday) {
	print "$buyorderuser{$key} to buy $buyorderquant{$key} of April $buyorderday{$key} for $buyorderprice{$key}<br>\n";
}
  print "<b>Sell Orders</b><br>\n";
	for $key (sort {$b <=> $a;} keys %sellorderday) {
		  print "$sellorderuser{$key} to sell $sellorderquant{$key} of April $sellorderday{$key} for $sellorderprice{$key}<br>\n";
	}

print "</td></tr></table>";

	print "</body></html>\n";